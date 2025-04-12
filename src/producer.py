#!/usr/bin/env python3
import json
import random
import time
import socket
from kafka import KafkaProducer
from clickhouse_driver import Client
from clickhouse_driver.errors import ServerException

# Configurazioni per Kafka
BROKER = 'kafka:9093'
TOPIC = 'gps_stream'
MESSAGES_PER_SECOND = 5

# Percorsi dei certificati per mutual TLS
SSL_CAFILE   = '/workspace/certs/ca.crt'
SSL_CERTFILE = '/workspace/certs/client_cert.pem'
SSL_KEYFILE  = '/workspace/certs/client_key.pem'

def wait_for_broker(host, port, timeout=2):
    """Attende che il broker Kafka sia raggiungibile sulla porta specificata."""
    while True:
        try:
            with socket.create_connection((host, port), timeout):
                print(f"Broker {host}:{port} disponibile")
                return
        except Exception as e:
            print(f"Attendo broker {host}:{port}... {e}")
            time.sleep(timeout)

# Funzione per verificare la presenza del database in ClickHouse
def wait_for_database(db_name, client, timeout=2, max_retries=30):
    """Attende finché il database specificato (db_name) esiste in ClickHouse."""
    retries = 0
    while retries < max_retries:
        try:
            databases = client.execute("SHOW DATABASES")
            databases_list = [db[0] for db in databases]
            if db_name in databases_list:
                print(f"Database '{db_name}' trovato in ClickHouse.")
                return True
            else:
                print(f"Database '{db_name}' non ancora disponibile. Riprovo...")
        except Exception as e:
            print(f"Errore durante la verifica del database: {e}")
        time.sleep(timeout)
        retries += 1
    raise Exception(f"Il database '{db_name}' non è stato trovato dopo {max_retries} tentativi.")

# Attendi che il broker Kafka sia raggiungibile
wait_for_broker('kafka', 9093)

# Opzionale: se desideri eseguire un controllo sul database (ad esempio per coordinarti con il consumer)
# Configura il client ClickHouse (usa il database 'nearyou' come target)
ch_client = Client(
    host='clickhouse-server',
    user='default',
    password='pwe@123@l@',
    port=9000,
    database='nearyou'
)

# Attende che il database "nearyou" sia stato creato in ClickHouse
try:
    wait_for_database("nearyou", ch_client)
except Exception as e:
    # Se il database non esiste dopo i tentativi, il producer può decidere di abbandonare
    # oppure continuare comunque; qui lo interrompiamo
    print(e)
    exit(1)

# Inizializza il KafkaProducer con mutual TLS
producer = KafkaProducer(
    bootstrap_servers=[BROKER],
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_random_gps():
    lat = random.uniform(45.40, 45.50)
    lon = random.uniform(9.10, 9.30)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "user_id": random.randint(1, 1000),
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp
    }

if __name__ == '__main__':
    print("Avvio del simulatore di dati GPS in modalità mutual TLS...")
    while True:
        message = generate_random_gps()
        producer.send(TOPIC, message)
        producer.flush()
        print(f"Inviato: {message}")
        time.sleep(1.0 / MESSAGES_PER_SECOND)
