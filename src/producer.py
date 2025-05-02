# src/producer.py
#!/usr/bin/env python3
"""
Invia in streaming su Kafka un punto GPS preso da un percorso “vero” in bici
su Milano, arricchito con un profilo utente prelevato dalla tabella users
in ClickHouse. Un messaggio al minuto.
"""
import json
import random
import time
import logging
from datetime import datetime, timezone

from kafka import KafkaProducer
import httpx
from faker import Faker
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    OSRM_URL,
    MILANO_MIN_LAT, MILANO_MAX_LAT,
    MILANO_MIN_LON, MILANO_MAX_LON,
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE,
)
from utils import wait_for_broker

setup_logging()
logger = logging.getLogger(__name__)

def fetch_route_osrm(start: str, end: str) -> list[dict]:
    url = f"{OSRM_URL}/route/v1/bicycle/{start};{end}"
    resp = httpx.get(
        url,
        params={"overview": "full", "geometries": "geojson"},
        timeout=10
    )
    resp.raise_for_status()
    coords = resp.json()["routes"][0]["geometry"]["coordinates"]
    return [{"lon": lon, "lat": lat, "time": None} for lon, lat in coords]

def random_point_in_bbox() -> tuple[float, float]:
    lat = random.uniform(MILANO_MIN_LAT, MILANO_MAX_LAT)
    lon = random.uniform(MILANO_MIN_LON, MILANO_MAX_LON)
    return lon, lat

# Attendi Kafka
logger.info("In attesa che Kafka sia disponibile…")
wait_for_broker("kafka", 9093)

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    security_protocol="SSL",
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
)
logger.info("Producer pronto sul topic %s", KAFKA_TOPIC)

# ClickHouse client per leggere i profili
ch = CHClient(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE
)
# Carica in memoria tutti i profili esistenti
users = ch.execute("SELECT user_id, age, profession, interests FROM users")
if not users:
    logger.error("Nessun utente trovato in ClickHouse: esegui generate_users prima.")
    exit(1)

# Primo percorso casuale
lon1, lat1 = random_point_in_bbox()
lon2, lat2 = random_point_in_bbox()
current_route = fetch_route_osrm(f"{lon1},{lat1}", f"{lon2},{lat2}")
idx = 0

# Loop di invio: un messaggio al minuto
while True:
    # Punto successivo
    pt = current_route[idx]
    idx += 1

    # Se finito, nuovo percorso
    if idx >= len(current_route):
        lon1, lat1 = random_point_in_bbox()
        lon2, lat2 = random_point_in_bbox()
        current_route = fetch_route_osrm(f"{lon1},{lat1}", f"{lon2},{lat2}")
        idx = 0
        pt = current_route[0]

    # Scegli un profilo esistente a caso
    uid, age, profession, interests = random.choice(users)

    # Costruisci il messaggio
    message = {
        "user_id": uid,
        "latitude": pt["lat"],
        "longitude": pt["lon"],
        "timestamp": pt["time"] or datetime.now(timezone.utc),
        "age": age,
        "profession": profession,
        "interests": interests,
        "shop_name": "",
        "shop_category": ""
    }

    # Invia e flush
    producer.send(KAFKA_TOPIC, message)
    producer.flush()
    logger.info("Inviato (%s): %s", uid, message)

    
    time.sleep(2)
