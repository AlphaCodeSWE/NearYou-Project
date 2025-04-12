#!/usr/bin/env python3
import json
import random
import time
import socket
from kafka import KafkaConsumer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

# Configurazioni Kafka
BROKER = 'kafka:9093'
TOPIC = 'gps_stream'
CONSUMER_GROUP = 'gps_consumers_group'

# Percorsi dei certificati per mutual TLS
SSL_CAFILE   = '/workspace/certs/ca.crt'
SSL_CERTFILE = '/workspace/certs/client_cert.pem'
SSL_KEYFILE  = '/workspace/certs/client_key.pem'

def wait_for_broker(host, port, timeout=2):
    while True:
        try:
            with socket.create_connection((host, port), timeout):
                print(f"Broker {host}:{port} disponibile")
                return
        except Exception as e:
            print(f"Attendo broker {host}:{port}... {e}")
            time.sleep(2)

# Attende che il broker Kafka sia raggiungibile
wait_for_broker('kafka', 9093)

# Inizializza il KafkaConsumer con mutual TLS
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[BROKER],
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    auto_offset_reset='earliest',
    group_id=CONSUMER_GROUP,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Connessione a ClickHouse
client = Client(
    host='clickhouse-server',
    user='default',
    password='pwe@123@l@',
    port=9000,
    database='nearyou'  # faccio un controllo succ per vedere se esiste
)

def wait_for_database(db_name, timeout=2, max_retries=30):
    """Attende che il database 'db_name' esista in ClickHouse."""
    retries = 0
    while retries < max_retries:
        try:
            databases = client.execute("SHOW DATABASES")
            databases_list = [db[0] for db in databases]
            if db_name in databases_list:
                print(f"Database '{db_name}' trovato.")
                return True
            else:
                print(f"Database '{db_name}' non ancora disponibile. Riprovo...")
        except Exception as e:
            print(f"Errore durante la verifica del database: {e}")
        time.sleep(timeout)
        retries += 1
    raise Exception(f"Il database '{db_name}' non è stato trovato dopo {max_retries} tentativi.")

# Attendi che il database 'nearyou' sia disponibile
wait_for_database('nearyou')

def generate_event_id():
    return random.randint(1000000000, 9999999999)

def create_table_if_not_exists():
    try:
        tables = client.execute("SHOW TABLES")
        tables_list = [t[0] for t in tables]
    except ServerException as e:
        print("Errore nel recuperare le tabelle:", e)
        tables_list = []
    if "user_events" not in tables_list:
        print("La tabella 'user_events' non esiste. Creandola...")
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
        print("La tabella 'user_events' esiste già.")

create_table_if_not_exists()

print("Consumer in ascolto sul topic:", TOPIC)
for message in consumer:
    data = message.value
    event = (
        generate_event_id(),    # event_id
        data['timestamp'],      # event_time
        data['user_id'],
        data['latitude'],
        data['longitude'],
        0.0,                    # poi_range
        '',                     # poi_name
        ''                      # poi_info
    )
    client.execute(
        'INSERT INTO user_events (event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info) VALUES',
        [event]
    )
    print("Inserito in DB:", event)
