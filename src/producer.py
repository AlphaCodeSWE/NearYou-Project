#!/usr/bin/env python3
import json
import random
import socket
from datetime import datetime, timezone
from kafka import KafkaProducer

# Configurazioni
BROKER = 'kafka:9093'
TOPIC = 'gps_stream'
MESSAGES_PER_SECOND = 5

# Percorsi dei certificati per mutual TLS
SSL_CAFILE   = '/workspace/certs/ca.crt'
SSL_CERTFILE = '/workspace/certs/client_cert.pem'
SSL_KEYFILE  = '/workspace/certs/client_key.pem'

#correggo l'errore del timestamp
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  
    raise TypeError("Tipo non serializzabile")

def wait_for_broker(host, port, timeout=2):
    """Attende che il broker Kafka sia raggiungibile sulla porta specificata 9093."""
    while True:
        try:
            with socket.create_connection((host, port), timeout):
                print(f"Broker {host}:{port} disponibile")
                return
        except Exception as e:
            print(f"Attendo broker {host}:{port}... {e}")
            time.sleep(timeout)

# Attende che il broker Kafka sia raggiungibile
wait_for_broker('kafka', 9093)

# Inizializza il KafkaProducer con mutual TLS
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
        "timestamp": timestamp_dt  # Oggetto datetime; verrà serializzato in ISO-8601
    }

if __name__ == '__main__':
    print("Avvio del simulatore di dati GPS in modalità mutual TLS...")
    while True:
        message = generate_random_gps()
        producer.send(TOPIC, message)
        producer.flush()
        print(f"Inviato: {message}")
        # Controlla che vengano inviati n messaggi al secondo
        import time
        time.sleep(1.0 / MESSAGES_PER_SECOND)
