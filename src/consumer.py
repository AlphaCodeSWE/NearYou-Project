#!/usr/bin/env python3
"""
Consuma gli eventi GPS dal topic Kafka, chiama il micro‑servizio
FastAPI (message‑generator) per creare un messaggio pubblicitario
personalizzato e infine salva tutto in ClickHouse.
"""
import json
import logging
import random
from datetime import datetime

import httpx
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
client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)

wait_for_clickhouse_database(client, CLICKHOUSE_DATABASE)


def create_table_if_missing() -> None:
    """Crea la tabella user_events se non esiste."""
    try:
        existing = [t[0] for t in client.execute("SHOW TABLES")]
    except ServerException as exc:
        logger.error("Errore SHOW TABLES: %s", exc)
        existing = []

    if "user_events" not in existing:
        logger.info("Creo tabella user_events …")
        client.execute("""
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
        logger.info("Tabella user_events già esistente.")


create_table_if_missing()

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

    # 2) recupera info sul negozio dal messaggio
    shop_name = data.get("shop_name", "Shop sconosciuto")
    shop_category = data.get("shop_category", "varie")

    # 3) chiamata al micro‑servizio LLM
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
                    "description": "",
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
        data.get("latitude", 0.0),
        data.get("longitude", 0.0),
        0.0,                    # poi_range placeholder
        shop_name,
        ad_text,
    )

    client.execute(
        """INSERT INTO user_events
           (event_id, event_time, user_id, latitude, longitude,
            poi_range, poi_name, poi_info)
           VALUES""",
        [event_tuple],
    )
    logger.info("Evento %s inserito", event_tuple[0])
