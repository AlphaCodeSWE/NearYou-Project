#!/usr/bin/env python3
import os
import asyncio
import ssl
import json
import logging                # ← aggiunto!
from datetime import datetime, timezone

import asyncpg
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
)
from utils import wait_for_broker

logger = logging.getLogger(__name__)
setup_logging()

async def wait_for_postgres(retries: int = 30, delay: int = 2):
    for i in range(retries):
        try:
            conn = await asyncpg.connect(
                host=POSTGRES_HOST, port=POSTGRES_PORT,
                user=POSTGRES_USER, password=POSTGRES_PASSWORD,
                database=POSTGRES_DB
            )
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto (tentativo %d/%d)", i+1, retries)
            await asyncio.sleep(delay)
    raise RuntimeError("Postgres non pronto dopo troppe prove")

async def wait_for_clickhouse(retries: int = 30, delay: int = 2):
    for i in range(retries):
        try:
            ch = CHClient(
                host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
                user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DATABASE
            )
            ch.execute("SELECT 1")
            logger.info("ClickHouse è pronto")
            return
        except Exception:
            logger.debug("ClickHouse non pronto (tentativo %d/%d)", i+1, retries)
            await asyncio.sleep(delay)
    raise RuntimeError("ClickHouse non pronto dopo troppe prove")

async def consumer_loop():
    # 1) Readiness
    host, port = KAFKA_BROKER.split(":")
    await asyncio.gather(
        asyncio.get_event_loop().run_in_executor(None, wait_for_broker, host, int(port)),
        wait_for_postgres(),
        wait_for_clickhouse(),
    )
    logger.info("Kafka, Postgres e ClickHouse sono pronti")

    # 2) SSL context per Kafka
    ssl_ctx = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_ctx.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)

    # 3) Inizializza consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_context=ssl_ctx,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    await consumer.start()

    # 4) Pool PostgreSQL e client ClickHouse
    pg_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        min_size=1, max_size=5
    )
    ch = CHClient(
        host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE
    )

    try:
        async for msg in consumer:
            data = msg.value
            try:
                # parse timestamp ISO -> datetime (rimuovo tzinfo per ClickHouse)
                ts = datetime.fromisoformat(data["timestamp"]).astimezone(timezone.utc).replace(tzinfo=None)

                # cerco il negozio più vicino
                row = await pg_pool.fetchrow(
                    """
                    SELECT
                      shop_id,
                      shop_name,
                      ST_Distance(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                      ) AS distance
                    FROM shops
                    ORDER BY distance
                    LIMIT 1
                    """,
                    data["longitude"], data["latitude"]
                )
                shop_id, shop_name, distance = row["shop_id"], row["shop_name"], row["distance"]

                # scrivo in ClickHouse
                ch.execute(
                    """
                    INSERT INTO user_events
                      (event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info)
                    VALUES
                    """,
                    [
                        (msg.offset,
                         ts,
                         data["user_id"],
                         data["latitude"],
                         data["longitude"],
                         distance,
                         shop_name,
                         "")  # poi_info vuoto
                    ]
                )
                logger.info(
                    "Utente %d → negozio più vicino '%s' (d=%.1fm)",
                    data["user_id"], shop_name, distance
                )
            except Exception as e:
                logger.error("Errore elaborazione messaggio %s: %s", msg, e)
    finally:
        await consumer.stop()
        await pg_pool.close()

if __name__ == "__main__":
    asyncio.run(consumer_loop())
