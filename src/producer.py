#!/usr/bin/env python3
"""
Invia in streaming su Kafka un punto GPS preso da un percorso “vero” in bici
su Milano, arricchito con un profilo utente prelevato dalla tabella users
in ClickHouse.
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
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE,
)
from utils import wait_for_broker

setup_logging()
logger = logging.getLogger(__name__)

def wait_for_osrm(url: str, interval: int = 30, max_retries: int = 500) -> None:
    """
    Attende che OSRM risponda almeno a una richiesta di healthcheck.
    Prova a richiedere un routing banale; considera OSRM pronto se non riceve un 5xx.
    Ripete ogni `interval` secondi fino a `max_retries` tentativi.
    """
    for attempt in range(1, max_retries + 1):
        try:
            r = httpx.get(
                f"{url}/route/v1/bicycle/0,0;0,0",
                params={"overview": "false"},
                timeout=10
            )
            if r.status_code < 500:
                logger.info("OSRM pronto (tentativo %d/%d).", attempt, max_retries)
                return
            else:
                logger.debug("OSRM risposta %d (tentativo %d/%d), riprovo tra %d s…",
                             r.status_code, attempt, max_retries, interval)
        except Exception as e:
            logger.debug("OSRM non raggiungibile (tentativo %d/%d): %s", attempt, max_retries, e)
        time.sleep(interval)
    raise RuntimeError(f"OSRM non pronto dopo {max_retries} tentativi.")

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

# 1) Attendi che Kafka sia disponibile
logger.info("In attesa che Kafka sia disponibile…")
wait_for_broker("kafka", 9093)

# 2) Attendi che OSRM sia disponibile (ogni 30s, fino a 500 volte)
logger.info("In attesa che OSRM sia disponibile…")
wait_for_osrm(OSRM_URL, interval=30, max_retries=500)

# 3) Imposta il producer Kafka
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

# 4) Carica i profili utenti da ClickHouse
ch = CHClient(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE
)
users = ch.execute("SELECT user_id, age, profession, interests FROM users")
if not users:
    logger.error("Nessun utente trovato in ClickHouse: esegui generate_users prima.")
    exit(1)

# 5) Estrai il primo percorso casuale da OSRM
lon1, lat1 = random_point_in_bbox()
lon2, lat2 = random_point_in_bbox()
current_route = fetch_route_osrm(f"{lon1},{lat1}", f"{lon2},{lat2}")
idx = 0

# 6) Ciclo di invio: un messaggio ogni 2 secondi
while True:
    pt = current_route[idx]
    idx += 1

    # Se ho finito il percorso, ne prendo uno nuovo
    if idx >= len(current_route):
        lon1, lat1 = random_point_in_bbox()
        lon2, lat2 = random_point_in_bbox()
        current_route = fetch_route_osrm(f"{lon1},{lat1}", f"{lon2},{lat2}")
        idx = 0
        pt = current_route[0]

    # Scegli un profilo utente casuale
    uid, age, profession, interests = random.choice(users)

    # Costruisci il payload del messaggio
    message = {
        "user_id":      uid,
        "latitude":     pt["lat"],
        "longitude":    pt["lon"],
        "timestamp":    pt["time"] or datetime.now(timezone.utc),
        "age":          age,
        "profession":   profession,
        "interests":    interests,
        "shop_name":    "",
        "shop_category": ""
    }

    # Invia su Kafka
    producer.send(KAFKA_TOPIC, message)
    producer.flush()
    logger.info("Inviato (%s): %s", uid, message)

    # Aspetta 2 secondi prima del prossimo punto (non faccio più aspettare)
    #time.sleep(2)
