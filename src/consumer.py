#!/usr/bin/env python3
import json
import random
from kafka import KafkaConsumer
from clickhouse_driver import Client

# Configurazioni
BROKER = 'kafka:9093'
TOPIC = 'gps_stream'
CONSUMER_GROUP = 'gps_consumers_group'

# Percorsi dei certificati per mutual TLS
SSL_CAFILE   = '/workspace/certs/ca.crt'
SSL_CERTFILE = '/workspace/certs/client_cert.pem'
SSL_KEYFILE  = '/workspace/certs/client_key.pem'

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

client = Client(
    host='clickhouse-server',
    user='default',
    password='pwe@123@l@',
    port=9000,
    database='nearyou'
)

def generate_event_id():
    return random.randint(1000000000, 9999999999)

def create_table_if_not_exists():
    tables = client.execute("SHOW TABLES")
    tables_list = [t[0] for t in tables]
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
