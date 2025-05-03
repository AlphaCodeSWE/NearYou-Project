#!/usr/bin/env python3
import os
import json
import asyncio
import logging
from datetime import datetime

import httpx
import psycopg2
from aiokafka import AIOKafkaConsumer
from aiokafka.structs import TopicPartition
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
    MESSAGE_GENERATOR_URL,
)
from utils import wait_for_broker

logger = logging.getLogger(__name__)
setup_logging()

# Quanti LLM call in parallelo
LLM_CONCURRENCY = 20

async def wait_services():
    # Kafka
    host, port = KAFKA_BROKER.split(":")
    await asyncio.get_event_loop().run_in_executor(None, wait_for_broker, host, int(port))
    logger.info(" Kafka è pronto")
    # Postgres
    await asyncio.get_event_loop().run_in_executor(None, wait_for_broker, POSTGRES_HOST, POSTGRES_PORT)
    logger.info(" Postgres è pronto")
    # ClickHouse
    await asyncio.get_event_loop().run_in_executor(None, wait_for_broker, CLICKHOUSE_HOST, CLICKHOUSE_PORT)
    logger.info(" ClickHouse è pronto")

async def wait_for_first_message(consumer: AIOKafkaConsumer):
    tp = TopicPartition(KAFKA_TOPIC, 0)
    while True:
        begin = await consumer.beginning_offsets([tp])
        end   = await consumer.end_offsets([tp])
        if end[tp] > begin[tp]:
            logger.info(" Trovato almeno un messaggio sul topic, comincio a consumare")
            return
        logger.debug("Nessun messaggio ancora (begin=%d, end=%d), riprovo tra 1s…", begin[tp], end[tp])
        await asyncio.sleep(1)

async def fetch_ad(user: dict, poi: dict) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(MESSAGE_GENERATOR_URL, json={"user": user, "poi": poi}, timeout=10.0)
        resp.raise_for_status()
        return resp.json().get("message", "")

async def handle_message(msg, pg_conn, pg_cur, ch, sem):
    event = json.loads(msg.value)
    lat, lon = event["latitude"], event["longitude"]

    # 1) lookup negozio in PostGIS
    pg_cur.execute(
        """
        SELECT shop_name, category
        FROM shops
        WHERE ST_DWithin(
          geom::geography,
          ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,
          200
        )
        ORDER BY ST_Distance(
          geom::geography,
          ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography
        )
        LIMIT 1
        """,
        (lon, lat, lon, lat)
    )
    shop_name, shop_cat = pg_cur.fetchone() or ("", "")

    # 2) generazione promo con semaforo
    async with sem:
        ad = await fetch_ad(
            {"age": event["age"], "profession": event["profession"], "interests": event["interests"]},
            {"name": shop_name or "negozio vicino", "category": shop_cat or "varie", "description": ""}
        )

    # 3) inserimento in ClickHouse
    ch.execute(
        """
        INSERT INTO user_events
          (event_id,event_time,user_id,latitude,longitude,poi_range,poi_name,poi_info)
        VALUES
        """,
        [(
            int(datetime.utcnow().timestamp() * 1e6) % 1_000_000_000,  # event_id pseudo‐unico
            datetime.fromisoformat(event["timestamp"]),
            event["user_id"],
            lat,
            lon,
            0.0,
            shop_name,
            ad
        )]
    )
    logger.debug("Processed user %d → poi='%s'", event["user_id"], shop_name or "N/A")

async def consumer_loop():
    # apro connessione sincrona a Postgres in executor
    loop = asyncio.get_event_loop()
    pg_conn = await loop.run_in_executor(
        None,
        lambda: psycopg2.connect(
            host=POSTGRES_HOST, port=POSTGRES_PORT,
            dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD
        )
    )
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # ClickHouse client
    ch = CHClient(
        host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE
    )

    # consumer async
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_cafile=SSL_CAFILE,
        ssl_certfile=SSL_CERTFILE,
        ssl_keyfile=SSL_KEYFILE,
        auto_offset_reset="earliest",
        group_id="gps_async_consumers"
    )
    await consumer.start()

    # aspetto il primo messaggio dal producer
    await wait_for_first_message(consumer)

    sem = asyncio.Semaphore(LLM_CONCURRENCY)
    try:
        async for msg in consumer:
            # lancio il task in background
            asyncio.create_task(handle_message(msg, pg_conn, pg_cur, ch, sem))
    finally:
        await consumer.stop()
        pg_cur.close()
        pg_conn.close()

if __name__ == "__main__":
    asyncio.run(wait_services())
    asyncio.run(consumer_loop())
