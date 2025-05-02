#!/usr/bin/env python3
"""
Invia in streaming su Kafka un punto GPS per ogni utente,
ciclando sui percorsi e rigenerandoli al termine.
"""
import json
import random
import time
import logging
from datetime import datetime, timezone

from kafka import KafkaProducer
import httpx
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    OSRM_URL,
    MILANO_MIN_LAT, MILANO_MAX_LAT,
    MILANO_MIN_LON, MILANO_MAX_LON,
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT, CLICKHOUSE_DATABASE,
)
from utils import wait_for_broker

setup_logging()
logger = logging.getLogger(__name__)

def wait_for_osrm(url: str, interval: int = 30, max_retries: int = 500) -> None:
    """Stesso healthcheck di prima."""
    for attempt in range(1, max_retries + 1):
        try:
            r = httpx.get(f"{url}/route/v1/bicycle/0,0;0,0",
                          params={"overview": "false"}, timeout=10)
            if r.status_code < 500:
                logger.info("OSRM pronto (tentativo %d/%d).", attempt, max_retries)
                return
        except Exception:
            pass
        time.sleep(interval)
    raise RuntimeError("OSRM non pronto dopo troppe volte.")

def fetch_route_osrm(start: str, end: str) -> list[dict]:
    """Restituisce lista di punti {lat, lon} per un percorso."""
    resp = httpx.get(
        f"{OSRM_URL}/route/v1/bicycle/{start};{end}",
        params={"overview": "full", "geometries": "geojson"},
        timeout=10
    )
    resp.raise_for_status()
    coords = resp.json()["routes"][0]["geometry"]["coordinates"]
    return [{"lon": lon, "lat": lat} for lon, lat in coords]

def random_point_in_bbox() -> tuple[float, float]:
    lat = random.uniform(MILANO_MIN_LAT, MILANO_MAX_LAT)
    lon = random.uniform(MILANO_MIN_LON, MILANO_MAX_LON)
    return lon, lat

# 1) Attendi i servizi
logger.info("Attendo Kafka…")
wait_for_broker("kafka", 9093)
logger.info("Attendo OSRM…")
wait_for_osrm(OSRM_URL)

# 2) Imposta il producer Kafka
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

# 3) Carica tutti i profili utenti da ClickHouse
ch = CHClient(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE
)
users = ch.execute("SELECT user_id, age, profession, interests FROM users")
if not users:
    logger.error("Nessun utente trovato: esegui generate_users prima.")
    exit(1)

# 4) Prepara un percorso e un indice per ciascun utente
user_routes = {}
route_indices = {}
for uid, age, profession, interests in users:
    # genera un percorso random iniziale
    lon1, lat1 = random_point_in_bbox()
    lon2, lat2 = random_point_in_bbox()
    route = fetch_route_osrm(f"{lon1},{lat1}", f"{lon2},{lat2}")
    user_routes[uid] = route
    route_indices[uid] = 0

logger.info("Setup completato per %d utenti.", len(users))

# 5) Loop principale: un invio per UTENTE a ogni iterazione
while True:
    for uid, age, profession, interests in users:
        idx = route_indices[uid]
        route = user_routes[uid]

        # Se il percorso è finito, rigenerane uno nuovo
        if idx >= len(route):
            lon1, lat1 = random_point_in_bbox()
            lon2, lat2 = random_point_in_bbox()
            route = fetch_route_osrm(f"{lon1},{lat1}", f"{lon2},{lat2}")
            user_routes[uid] = route
            idx = 0

        pt = route[idx]
        route_indices[uid] = idx + 1

        # Costruisci e invia il messaggio
        message = {
            "user_id":      uid,
            "latitude":     pt["lat"],
            "longitude":    pt["lon"],
            "timestamp":    datetime.now(timezone.utc),
            "age":          age,
            "profession":   profession,
            "interests":    interests,
        }
        producer.send(KAFKA_TOPIC, message)
        logger.info("Inviato per utente %s: %s", uid, message)

    # Attendi 2 secondi prima della prossima tornata
    #time.sleep(2)
