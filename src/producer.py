#!/usr/bin/env python3
import json
import random
import socket
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

# Configurazioni Kafka
BROKER = 'kafka:9093'
TOPIC = 'gps_stream'
MESSAGES_PER_SECOND = 5

# Percorsi dei certificati per mutual TLS
SSL_CAFILE   = '/workspace/certs/ca.crt'
SSL_CERTFILE = '/workspace/certs/client_cert.pem'
SSL_KEYFILE  = '/workspace/certs/client_key.pem'

def json_serializer(obj):
    """Serializza un oggetto datetime in formato ISO-8601."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Tipo non serializzabile")

def wait_for_broker(host, port, timeout=2):
    """Attende che il broker Kafka sia raggiungibile sulla porta 9093."""
    while True:
        try:
            with socket.create_connection((host, port), timeout):
                print(f"Broker {host}:{port} disponibile")
                return
        except Exception as e:
            print(f"Attendo broker {host}:{port}... {e}")
            time.sleep(timeout)

def wait_for_database(db_name, client, timeout=2, max_retries=30):
    """Attende finché il database 'nearyou' esiste in ClickHouse."""
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

# Attendi che il broker Kafka sia disponibile
wait_for_broker('kafka', 9093)

# Configura il client ClickHouse per controllare il database
ch_client = Client(
    host='clickhouse-server',
    user='default',
    password='pwe@123@l@',
    port=9000,
    database='nearyou'
)

# Attendi che il database "nearyou" sia disponibile in ClickHouse
try:
    wait_for_database("nearyou", ch_client)
except Exception as e:
    print(e)
    exit(1)

# Inizializza il KafkaProducer con mutual TLS e custom serializer per datetime
producer = KafkaProducer(
    bootstrap_servers=[BROKER],
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    value_serializer=lambda v: json.dumps(v, default=json_serializer).encode('utf-8')
)

def generate_random_gps():
    lat = random.uniform(45.40, 45.50)
    lon = random.uniform(9.10, 9.30)
    # Genera un timestamp come oggetto datetime in UTC
    timestamp_dt = datetime.now(timezone.utc)
    return {
        "user_id": random.randint(1, 1000),
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp_dt  # Verrà serializzato in ISO-8601
    }

if __name__ == '__main__':
    print("Avvio del simulatore di dati GPS in modalità mutual TLS...")
    while True:
        message = generate_random_gps()
        producer.send(TOPIC, message)
        producer.flush()
        print(f"Inviato: {message}")
        time.sleep(1.0 / MESSAGES_PER_SECOND)
