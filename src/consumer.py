#!/usr/bin/env python3
"""
Consumer Kafka → arricchisce gli eventi GPS con i POI di Milano
(lookup PostGIS) → chiama l'LLM → salva in ClickHouse.
"""

import json
import logging
import random
from datetime import datetime

import httpx
import psycopg2                     # <-- NEW
from kafka import KafkaConsumer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

from logger_config import setup_logging
from utils import wait_for_broker
from db_utils import wait_for_clickhouse_database
from configg import (
    # --- Kafka ---
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    # --- ClickHouse ---
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    # --- Postgres ---
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER,
    POSTGRES_PASSWORD, POSTGRES_DB,
    # --- micro-servizio LLM ---
    MESSAGE_GENERATOR_URL,
)

# --------------------------------------------------------------------------- #
# logging & readiness
# --------------------------------------------------------------------------- #
setup_logging()
logger = logging.getLogger(__name__)

logger.info("Attendo Kafka …")
wait_for_broker("kafka", 9093)

# --------------------------------------------------------------------------- #
# Kafka consumer
# --------------------------------------------------------------------------- #
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

# --------------------------------------------------------------------------- #
# ClickHouse
# --------------------------------------------------------------------------- #
ch = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)
wait_for_clickhouse_database(ch, CLICKHOUSE_DATABASE)

def ensure_ch_table():
    try:
        present = [t[0] for t in ch.execute("SHOW TABLES")]
    except ServerException as exc:
        logger.error("SHOW TABLES ClickHouse: %s", exc)
        present = []
    if "user_events" not in present:
        logger.info("Creo tabella user_events …")
        ch.execute("""
            CREATE TABLE user_events (
                event_id   UInt64,
                event_time DateTime,
                user_id    UInt64,
                latitude   Float64,
                longitude  Float64,
                poi_range  Float64,
                poi_name   String,
                poi_info   String
            ) ENGINE = MergeTree()
            ORDER BY event_id
        """)

ensure_ch_table()

# --------------------------------------------------------------------------- #
# PostGIS connection
# --------------------------------------------------------------------------- #
pg = psycopg2.connect(
    host=POSTGRES_HOST or "postgres",
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
)
pg.autocommit = True
pg_cur = pg.cursor()

def nearest_shop(lat: float, lon: float, max_m: int = 200):
    """
    Ritorna (shop_name, category) del negozio più vicino entro max_m metri,
    oppure (None, None) se non trovato.
    """
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

# --------------------------------------------------------------------------- #
# consume loop
# --------------------------------------------------------------------------- #
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

    # 2) lookup POI
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
                    "name":     shop_name or "negozio vicino",
                    "category": shop_cat  or "varie",
                    "description": "",
                },
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        ad_text = resp.json()["message"]
    except Exception as exc:
        logger.error("Errore LLM: %s", exc)
        ad_text = ""

    # 4) inserimento in ClickHouse
    record = (
        random.randint(1_000_000_000, 9_999_999_999),  # event_id
        ts,
        event["user_id"],
        lat,
        lon,
        0.0,                # poi_range (placeholder)
        shop_name,
        ad_text,
    )
    ch.execute("""
        INSERT INTO user_events
        (event_id,event_time,user_id,latitude,longitude,poi_range,poi_name,poi_info)
        VALUES
    """, [record])

    logger.info("Evento %s inserito - poi_name='%s'", record[0], shop_name or "N/A")
