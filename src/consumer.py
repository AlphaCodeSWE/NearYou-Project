# src/consumer.py
#!/usr/bin/env python3
import json
import random
import time
from datetime import datetime
import logging
from kafka import KafkaConsumer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException
from db_utils import wait_for_clickhouse_database

from logger_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE
)

from utils import wait_for_broker

# Attendi che il broker Kafka sia disponibile
wait_for_broker('kafka', 9093)

# Inizializza il consumer Kafka
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    auto_offset_reset='earliest',
    group_id=CONSUMER_GROUP,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Inizializza il client ClickHouse
client = Client(
    host=CLICKHOUSE_HOST,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    port=CLICKHOUSE_PORT,
    database=CLICKHOUSE_DATABASE
)

# Attendi la disponibilità del database ClickHouse
wait_for_clickhouse_database(client, CLICKHOUSE_DATABASE)

def create_table_if_not_exists() -> None:
    try:
        tables = client.execute("SHOW TABLES")
        tables_list = [t[0] for t in tables]
    except ServerException as e:
        logger.error("Errore nel recuperare le tabelle: %s", e)
        tables_list = []
    if "user_events" not in tables_list:
        logger.info("La tabella 'user_events' non esiste. Creandola...")
        client.execute('''
            CREATE TABLE IF NOT EXISTS user_events (
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
        ''')
    else:
        logger.info("La tabella 'user_events' esiste già.")

create_table_if_not_exists()

logger.info("Consumer in ascolto sul topic: %s", KAFKA_TOPIC)
for message in consumer:
    data = message.value
    try:
        timestamp_dt = datetime.fromisoformat(data['timestamp'])
    except Exception as e:
        logger.error("Errore nella conversione del timestamp: %s -> %s", data['timestamp'], e)
        continue
    event = (
        random.randint(1000000000, 9999999999),  # event_id
        timestamp_dt,
        data.get('user_id', 0),
        data.get('latitude', 0.0),
        data.get('longitude', 0.0),
        0.0,  # poi_range di default
        '',   # poi_name di default
        ''    # poi_info di default
    )
    client.execute(
        'INSERT INTO user_events (event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info) VALUES',
        [event]
    )
    logger.info("Inserito in DB: %s", event)
