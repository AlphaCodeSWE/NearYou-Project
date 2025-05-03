#!/usr/bin/env python3
import os
import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient
import asyncpg

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
)

logger = logging.getLogger(__name__)
setup_logging()

async def wait_for_kafka(interval: int = 5):
    host, port = KAFKA_BROKER.split(":")
    # utils.wait_for_broker è sync
    from utils import wait_for_broker
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, wait_for_broker, host, int(port))
    logger.info("Kafka è pronto")

async def wait_for_postgres(max_retries: int = 30, interval: int = 2):
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(
                host=POSTGRES_HOST, port=POSTGRES_PORT,
                user=POSTGRES_USER, password=POSTGRES_PASSWORD,
                database=POSTGRES_DB
            )
            await conn.execute("SELECT 1")
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto (tentativo %d/%d)", i+1, max_retries)
            await asyncio.sleep(interval)
    raise RuntimeError("Postgres non pronto")

async def wait_for_clickhouse(max_retries: int = 30, interval: int = 2):
    for i in range(max_retries):
        try:
            client = CHClient(
                host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
                user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DATABASE
            )
            client.execute("SELECT 1")
            logger.info("ClickHouse è pronto")
            return
        except Exception:
            logger.debug("ClickHouse non pronto (tentativo %d/%d)", i+1, max_retries)
            await asyncio.sleep(interval)
    raise RuntimeError("ClickHouse non pronto")

async def consumer_loop():
    # 1) Readiness checks
    await asyncio.gather(
        wait_for_kafka(),
        wait_for_postgres(),
        wait_for_clickhouse(),
    )

    # 2) Connessione a ClickHouse (sincrona)
    ch = CHClient(
        host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE
    )

    # 3) Pool asyncpg per leggere shops
    pg_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD,
        database=POSTGRES_DB, min_size=1, max_size=5
    )

    # 4) Setup consumer Kafka
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_cafile=SSL_CAFILE,
        ssl_certfile=SSL_CERTFILE,
        ssl_keyfile=SSL_KEYFILE,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda b: json.loads(b.decode("utf-8"))
    )
    await consumer.start()

    try:
        async for msg in consumer:
            data = msg.value
            # 5) Trova negozio più vicino in Postgres (usando <-> index)
            row = await pg_pool.fetchrow(
                """
                SELECT id, name, category,
                  ST_DistanceSphere(location, ST_MakePoint($1, $2)) AS distance
                FROM shops
                ORDER BY location <-> ST_MakePoint($1, $2)
                LIMIT 1
                """,
                data["longitude"], data["latitude"]
            )
            shop_id   = row["id"]
            shop_name = row["name"]
            distance  = row["distance"]

            # 6) Inserisci l’evento in ClickHouse
            ch.execute(
                """
                INSERT INTO user_events
                  (user_id, latitude, longitude, timestamp, age, profession, interests, shop_id, shop_name, distance)
                VALUES
                """,
                [(
                    data["user_id"],
                    data["latitude"],
                    data["longitude"],
                    data["timestamp"],
                    data.get("age"),
                    data.get("profession"),
                    data.get("interests"),
                    shop_id,
                    shop_name,
                    distance
                )]
            )
            logger.debug(
                "Evento user %d → shop %s (%.1f m)",
                data["user_id"], shop_name, distance
            )
    finally:
        await consumer.stop()
        await pg_pool.close()

if __name__ == "__main__":
    asyncio.run(consumer_loop())
