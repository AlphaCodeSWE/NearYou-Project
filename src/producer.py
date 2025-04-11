#!/usr/bin/env python3
import json
import random
import time
import socket
from kafka import KafkaProducer

# Configurazioni
BROKER = 'kafka:9093'
TOPIC = 'gps_stream'
MESSAGES_PER_SECOND = 5

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

# Inizializza il KafkaProducer con configurazione mutual TLS
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
