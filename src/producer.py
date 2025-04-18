#!/usr/bin/env python3
"""
Invia in streaming su Kafka una serie di eventi GPS arricchiti
con semplici informazioni di profilo utente (età, professione, interessi).
Il broker utilizza SSL mutual‑TLS, i percorsi dei certificati arrivano da configg.py
"""
import json
import random
import time
from datetime import datetime, timezone
import logging

from kafka import KafkaProducer
from faker import Faker

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
)

from utils import wait_for_broker

setup_logging()
logger = logging.getLogger(__name__)
fake = Faker("it_IT")

# ---------- Helper -----------------------------------------------------------


def json_serializer(obj):
    """Converte le date in ISO‑8601 per KafkaProducer."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Oggetto non serializzabile: {type(obj)}")


def generate_random_profile() -> dict:
    """Crea un mini‑profilo utente plausibile."""
    professions = ["Designer", "Sviluppatore", "Studente", "Medico",
                   "Insegnante", "Ingegnere", "Commercialista"]
    interests_pool = ["caffè", "bicicletta", "arte", "cinema",
                      "fitness", "libri", "fotografia", "musica"]
    return {
        "age": random.randint(18, 70),
        "profession": random.choice(professions),
        "interests": ", ".join(random.sample(interests_pool, k=2))
    }


def generate_random_gps_message() -> dict:
    """Crea il payload da inviare: GPS + user profiling."""
    lat = random.uniform(45.40, 45.50)      # Milano circa
    lon = random.uniform(9.10, 9.30)

    user_id = random.randint(1, 1000)
    profile = generate_random_profile()

    # Per esempio scegli uno shop casuale (potrà essere mappato dal consumer)
    shops = [
        ("Caffè Arte", "caffetteria"),
        ("BiciRent", "noleggio"),
        ("Ristorante Belvedere", "ristorante")
    ]
    shop_name, shop_cat = random.choice(shops)

    return {
        "user_id": user_id,
        "latitude": lat,
        "longitude": lon,
        "timestamp": datetime.now(timezone.utc),     # serializzato in ISO
        "age": profile["age"],
        "profession": profile["profession"],
        "interests": profile["interests"],
        "shop_name": shop_name,
        "shop_category": shop_cat
    }


# ---------- Start‑up ---------------------------------------------------------
logger.info("In attesa che Kafka (SSL) sia disponibile …")
wait_for_broker("kafka", 9093)

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    security_protocol="SSL",
    ssl_check_hostname=True,
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    value_serializer=lambda v: json.dumps(v, default=json_serializer).encode("utf-8"),
)

logger.info("Producer pronto: topic=%s", KAFKA_TOPIC)

BATCH_SIZE = 5
batch_counter = 0

while True:
    message = generate_random_gps_message()
    producer.send(KAFKA_TOPIC, message)
    batch_counter += 1
    logger.debug("Messaggio enqueued: %s", message)

    if batch_counter >= BATCH_SIZE:
        producer.flush()
        logger.info("Batch di %d messaggi inviato", BATCH_SIZE)
        batch_counter = 0

    time.sleep(0.2)          # ~5 messaggi al secondo
