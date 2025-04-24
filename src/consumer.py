#!/usr/bin/env python3
"""
Consuma gli eventi GPS dal topic Kafka, arricchisce ciascun evento
trovando in PostGIS il negozio più vicino, chiama il micro-servizio
FastAPI (message-generator) per creare un messaggio promozionale,
e infine salva tutto in ClickHouse.
"""
import json
import logging
import random
from datetime import datetime

import httpx
import psycopg2
from kafka import KafkaConsumer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

from logger_config import setup_logging
from utils import wait_for_broker
from db_utils import wait_for_clickhouse_database
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    MESSAGE_GENERATOR_URL,
    POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
)

# ---------- logging ----------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

# ---------- readiness --------------------------------------------------------
logger.info("Attendo Kafka …")
wait_for_broker("kafka", 9093)

# ---------- Kafka consumer ---------------------------------------------------
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

# ---------- ClickHouse client -----------------------------------------------
ch_client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)
wait_for_clickhouse_database(ch_client, CLICKHOUSE_DATABASE)

# ---------- Postgres client -------------------------------------------------
pg_conn = psycopg2.connect(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    dbname=POSTGRES_DB
)
pg_conn.autocommit = True
pg_cur = pg_conn.cursor()

def create_ch_table_if_missing() -> None:
    """Crea la tabella user_events in ClickHouse se non esiste."""
    try:
        existing = [t[0] for t in ch_client.execute("SHOW TABLES")]
    except ServerException as exc:
        logger.error("Errore SHOW TABLES ClickHouse: %s", exc)
        existing = []
    if "user_events" not in existing:
        logger.info("Creo tabella user_events in ClickHouse …")
        ch_client.execute("""
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
    else:
        logger.info("Tabella user_events già esistente in ClickHouse.")

create_ch_table_if_missing()

# ---------- loop di consumo --------------------------------------------------
logger.info("Consumer in ascolto sul topic: %s", KAFKA_TOPIC)

for message in consumer:
    data = message.value

    # 1) parsing timestamp
    try:
        ts_dt = datetime.fromisoformat(data["timestamp"])
    except (KeyError, ValueError) as exc:
        logger.error("Timestamp non valido: %s", exc)
        continue

    lat = data.get("latitude")
    lon = data.get("longitude")

    # 2) trovo il negozio più vicino in Postgres/PostGIS
    pg_cur.execute("""
        SELECT
            shop_name,
            category,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS dist_m
        FROM shops
        ORDER BY dist_m
        LIMIT 1;
    """, (lon, lat))
    row = pg_cur.fetchone()
    if row:
        shop_name, shop_category, poi_range = row
    else:
        shop_name, shop_category, poi_range = "Nessun negozio vicino", "", None

    # 3) chiamata al micro-servizio LLM
    try:
        resp = httpx.post(
            MESSAGE_GENERATOR_URL,
            json={
                "user": {
                    "age": data.get("age", 0),
                    "profession": data.get("profession", ""),
                    "interests": data.get("interests", ""),
                },
                "poi": {
                    "name": shop_name,
                    "category": shop_category,
                    "description": f"Distanza: {int(poi_range)} m" if poi_range is not None else ""
                },
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        ad_text = resp.json()["message"]
    except Exception as exc:
        logger.error("Errore chiamata LLM: %s", exc)
        ad_text = ""

    # 4) inserimento in ClickHouse
    event_tuple = (
        random.randint(1_000_000_000, 9_999_999_999),  # event_id
        ts_dt,
        data.get("user_id", 0),
        lat,
        lon,
        poi_range or 0.0,
        shop_name,
        ad_text,
    )

    ch_client.execute(
        """INSERT INTO user_events
           (event_id, event_time, user_id, latitude, longitude,
            poi_range, poi_name, poi_info)
           VALUES""",
        [event_tuple],
    )
    logger.info("Evento %s inserito (shop: %s, dist: %s m)",
                event_tuple[0], shop_name, poi_range)
