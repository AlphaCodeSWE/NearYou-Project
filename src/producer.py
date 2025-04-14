#!/usr/bin/env python3
import json
import random
import socket
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException
import logging

from logger_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Importa configurazioni
from config import KAFKA_BROKER, KAFKA_TOPIC, SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE

# Funzione di utilità
from utils import wait_for_broker

# Attendi che il broker Kafka sia disponibile
wait_for_broker('kafka', 9093)

# Configura il client ClickHouse per controllare il database (opzionale, se serve verificarne la presenza)
ch_client = Client(
    host=CLICKHOUSE_HOST,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    port=CLICKHOUSE_PORT,
    database=CLICKHOUSE_DATABASE
)

def wait_for_database(db_name: str, client: Client, timeout: int = 2, max_retries: int = 30) -> bool:
    """
    Attende finché il database specificato esiste in ClickHouse.
    
    Parameters:
        db_name (str): Nome del database.
        client (Client): Istanza del client ClickHouse.
        timeout (int): Tempo in secondi tra i tentativi.
        max_retries (int): Numero massimo di tentativi.
        
    Returns:
        bool: True se il database è disponibile.
    """
    retries = 0
    while retries < max_retries:
        try:
            databases = client.execute("SHOW DATABASES")
            databases_list = [db[0] for db in databases]
            if db_name in databases_list:
                logger.info("Database '%s' trovato.", db_name)
                return True
            else:
                logger.info("Database '%s' non ancora disponibile. Riprovo...", db_name)
        except Exception as e:
            logger.error("Errore durante la verifica del database: %s", e)
        time.sleep(timeout)
        retries += 1
    raise Exception(f"Il database '{db_name}' non è stato trovato dopo {max_retries} tentativi.")

# Attendi che il database "nearyou" sia disponibile in ClickHouse
try:
    wait_for_database(CLICKHOUSE_DATABASE, ch_client)
except Exception as e:
    logger.error(e)
    exit(1)

def json_serializer(obj):
    """
    Serializza un oggetto datetime in formato ISO-8601.
    """
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
    """
    Genera dati GPS casuali e un timestamp in UTC.
    
    Returns:
        dict: Dizionario con user_id, latitude, longitude e timestamp.
    """
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
    while True:
        message = generate_random_gps()
        producer.send(KAFKA_TOPIC, message)
        producer.flush()
        logger.info("Inviato: %s", message)
        time.sleep(1.0 / 5)  # 5 messaggi al secondo
