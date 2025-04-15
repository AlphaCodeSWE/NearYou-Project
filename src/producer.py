# src/producer.py
#!/usr/bin/env python3
import json
import random
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
import logging

from logger_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from configg import KAFKA_BROKER, KAFKA_TOPIC, SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE
from configg import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE

from utils import wait_for_broker

# Attendi che il broker Kafka sia disponibile
wait_for_broker('kafka', 9093)

def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Tipo non serializzabile")

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    value_serializer=lambda v: json.dumps(v, default=json_serializer).encode('utf-8')
)

def generate_random_gps() -> dict:
    lat = random.uniform(45.40, 45.50)
    lon = random.uniform(9.10, 9.30)
    timestamp_dt = datetime.now(timezone.utc)
    return {
        "user_id": random.randint(1, 1000),
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp_dt  # Verrà serializzato in ISO-8601
    }

if __name__ == '__main__':
    logger.info("Avvio del simulatore di dati GPS in modalità mutual TLS...")
    batch_size = 5  # Numero di messaggi da inviare prima del flush
    batch_count = 0
    while True:
        message = generate_random_gps()
        producer.send(KAFKA_TOPIC, message)
        batch_count += 1
        logger.info("Messaggio aggiunto al batch: %s", message)
        
        if batch_count >= batch_size:
            producer.flush()
            logger.info("Batch di %d messaggi inviato.", batch_size)
            batch_count = 0
        
        time.sleep(1.0 / 5)  # 5 messaggi al secondo
