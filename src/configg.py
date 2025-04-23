# src/configg.py
import os
from dotenv import load_dotenv

load_dotenv()  # Carica le variabili dall’ambiente 

# Configurazione Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9093")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "gps_stream")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "gps_consumers_group")

# Configurazione percorsi certificati
SSL_CAFILE = os.getenv("SSL_CAFILE", "/workspace/certs/ca.crt")
SSL_CERTFILE = os.getenv("SSL_CERTFILE", "/workspace/certs/client_cert.pem")
SSL_KEYFILE = os.getenv("SSL_KEYFILE", "/workspace/certs/client_key.pem")

# Configurazione ClickHouse
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse-server")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "pwe@123@l@")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "9000"))
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "nearyou")

# Configurazione Postgres
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres-postgis")
POSTGRES_USER = os.getenv("POSTGRES_USER", "nearuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nearypass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "near_you_shops")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

# URL del micro‑servizio che genera i messaggi
MESSAGE_GENERATOR_URL = os.getenv(
    "MESSAGE_GENERATOR_URL",
    "http://message-generator:8001/generate",
)


# Google Maps JS API Key
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Firebase App Check config
FIREBASE_API_KEY            = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_AUTH_DOMAIN        = os.getenv("FIREBASE_AUTH_DOMAIN", "")
FIREBASE_PROJECT_ID         = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_RECAPTCHA_SITE_KEY = os.getenv("FIREBASE_RECAPTCHA_SITE_KEY", "")
