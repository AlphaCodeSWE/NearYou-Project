#!/usr/bin/env python3
"""
Consumer Kafka → arricchisce gli eventi GPS con i POI di Milano
(lookup PostGIS) → chiama l'LLM → salva in ClickHouse.
"""

import json
import logging
import random
import time
from datetime import datetime

import httpx
import psycopg2
from kafka import KafkaConsumer, TopicPartition
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

from logger_config import setup_logging
from utils import wait_for_broker
from db_utils import wait_for_clickhouse_database
from configg import (
    # Kafka
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    # ClickHouse
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    # Postgres
    POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
    # micro-servizio LLM
    MESSAGE_GENERATOR_URL,
)

# ─── logging & readiness ────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# 1) Attendo Kafka
logger.info("Attendo Kafka …")
wait_for_broker("kafka", 9093)

# 2) Attendo Postgres (porta TCP)
logger.info("Attendo Postgres …")
wait_for_broker(POSTGRES_HOST, POSTGRES_PORT)

# 3) Attendo ClickHouse (porta TCP)
logger.info("Attendo ClickHouse …")
wait_for_broker("clickhouse-server", CLICKHOUSE_PORT)

# ─── ClickHouse client & schema readiness ──────────────────────────────────
ch = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)

# 4) Attendo che il database esista
wait_for_clickhouse_database(ch, CLICKHOUSE_DATABASE)

# 5) Attendo che le tabelle ClickHouse siano già create
def wait_for_ch_table(table_name: str, client: Client, interval: int = 2, max_retries: int = 30):
    retries = 0
    while retries < max_retries:
        try:
            existing = [t[0] for t in client.execute("SHOW TABLES")]
            if table_name in existing:
                logger.info(f"Tabella ClickHouse '{table_name}' pronta.")
                return
        except ServerException as e:
            logger.warning(f"Errore controllo tabella '{table_name}': {e}")
        time.sleep(interval)
        retries += 1
    raise RuntimeError(f"Tabella ClickHouse '{table_name}' non trovata dopo {max_retries} tentativi.")

wait_for_ch_table("users",       ch)
wait_for_ch_table("user_events", ch)

# ─── Kafka consumer setup ───────────────────────────────────────────────────
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    security_protocol="SSL",
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    auto_offset_reset="earliest",
    group_id=CONSUMER_GROUP,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

# 6) Verifica che il producer abbia già inviato almeno un messaggio
logger.info("Controllo che il producer abbia pubblicato almeno un messaggio…")
tp = TopicPartition(KAFKA_TOPIC, 0)
for _ in range(6):
    begin = consumer.beginning_offsets([tp])[tp]
    end   = consumer.end_offsets([tp])[tp]
    if end > begin:
        logger.info("Trovati %d messaggi sul topic %s → parto.", end - begin, KAFKA_TOPIC)
        break
    logger.warning("Nessun messaggio ancora (begin=%d, end=%d), riprovo tra 5s…", begin, end)
    time.sleep(5)
else:
    raise RuntimeError(f"Il producer non sembra aver inviato nulla su {KAFKA_TOPIC} dopo 30s.")

# ─── PostGIS connection ─────────────────────────────────────────────────────
logger.info("Apro connessione a Postgres …")
pg = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
)
pg.autocommit = True
pg_cur = pg.cursor()

def nearest_shop(lat: float, lon: float, max_m: int = 200):
    sql = """
        SELECT shop_name, category
        FROM shops
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        )
        ORDER BY ST_Distance(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
        )
        LIMIT 1;
    """
    pg_cur.execute(sql, (lon, lat, max_m, lon, lat))
    row = pg_cur.fetchone()
    return row if row else (None, None)

# ─── consume loop ───────────────────────────────────────────────────────────
logger.info("Consumer in ascolto su topic: %s", KAFKA_TOPIC)

for msg in consumer:
    event = msg.value

    # 1) timestamp
    try:
        ts = datetime.fromisoformat(event["timestamp"])
    except (KeyError, ValueError) as exc:
        logger.warning("Timestamp malformato: %s", exc)
        continue

    lat, lon = event["latitude"], event["longitude"]

    # 2) lookup POI in PostGIS
    shop_name, shop_cat = nearest_shop(lat, lon)
    shop_name = shop_name or ""
    shop_cat  = shop_cat  or ""

    # 3) chiamata micro-servizio LLM
    try:
        resp = httpx.post(
            MESSAGE_GENERATOR_URL,
            json={
                "user": {
                    "age":        event["age"],
                    "profession": event["profession"],
                    "interests":  event["interests"],
                },
                "poi": {
                    "name":        shop_name or "negozio vicino",
                    "category":    shop_cat  or "varie",
                    "description": "",
                },
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        ad_text = resp.json().get("message", "")
    except Exception as exc:
        logger.error("Errore LLM: %s", exc)
        ad_text = ""

    # 4) inserimento in ClickHouse
    record = (
        random.randint(1_000_000_000, 9_999_999_999),
        ts,
        event["user_id"],
        lat,
        lon,
        0.0,
        shop_name,
        ad_text,
    )
    ch.execute(
        "INSERT INTO user_events "
        "(event_id,event_time,user_id,latitude,longitude,poi_range,poi_name,poi_info) "
        "VALUES",
        [record]
    )

    logger.info("Evento %s inserito - poi_name='%s'", record[0], shop_name or "N/A")
