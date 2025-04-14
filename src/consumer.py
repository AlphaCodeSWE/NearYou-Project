#!/usr/bin/env python3
import json
import random
import time
from datetime import datetime
from kafka import KafkaConsumer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException
import logging

# Inizializza il logging
from logger_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Importa configurazioni da config.py
from config import KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP, SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE

# Funzione di utilità per l'attesa del broker
from utils import wait_for_broker

# Attendi che il broker Kafka sia disponibile
wait_for_broker('kafka', 9093)

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

client = Client(
    host=CLICKHOUSE_HOST,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    port=CLICKHOUSE_PORT,
    database=CLICKHOUSE_DATABASE
)

def wait_for_database(db_name: str, timeout: int = 2, max_retries: int = 30) -> bool:
    """
    Attende finché il database specificato esiste in ClickHouse.
    
    Parameters:
        db_name (str): Nome del database.
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
                logger.info(f"Database '{db_name}' trovato.")
                return True
            else:
                logger.info(f"Database '{db_name}' non ancora disponibile. Riprovo...")
        except Exception as e:
            logger.error(f"Errore nella verifica del database: {e}")
        time.sleep(timeout)
        retries += 1
    raise Exception(f"Il database '{db_name}' non è stato trovato dopo {max_retries} tentativi.")

# Attendi che il database "nearyou" sia disponibile
wait_for_database(CLICKHOUSE_DATABASE, timeout=2, max_retries=30)

def generate_event_id() -> int:
    """
    Genera un identificatore unico per l'evento.
    
    Returns:
        int: Identificatore generato.
    """
    return random.randint(1000000000, 9999999999)

def create_table_if_not_exists() -> None:
    """
    Verifica se la tabella 'user_events' esiste; in caso contrario, la crea.
    """
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
        # Converte la stringa ISO-8601 in un oggetto datetime.
        timestamp_dt = datetime.fromisoformat(data['timestamp'])
    except Exception as e:
        logger.error("Errore nella conversione del timestamp: %s -> %s", data['timestamp'], e)
        continue  # Salta il messaggio se la conversione fallisce

    event = (
        generate_event_id(),    # event_id
        timestamp_dt,           # event_time
        data.get('user_id', 0),
        data.get('latitude', 0.0),
        data.get('longitude', 0.0),
        0.0,                    # poi_range (valore di default)
        '',                     # poi_name
        ''                      # poi_info
    )
    client.execute(
        'INSERT INTO user_events (event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info) VALUES',
        [event]
    )
    logger.info("Inserito in DB: %s", event)
