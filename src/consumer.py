#!/usr/bin/env python3
import asyncio
import ssl
import json
import logging
from datetime import datetime, timezone

import asyncpg
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER,
    KAFKA_TOPIC,
    CONSUMER_GROUP,
    SSL_CAFILE,
    SSL_CERTFILE,
    SSL_KEYFILE,
    CLICKHOUSE_HOST,
    CLICKHOUSE_PORT,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_DATABASE,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
)
from utils import wait_for_broker

logger = logging.getLogger(__name__)
setup_logging()

async def wait_for_clickhouse(retries: int = 30, interval: int = 2):
    for i in range(retries):
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
            logger.debug("ClickHouse non pronto (tentativo %d/%d)", i+1, retries)
            await asyncio.sleep(interval)
    raise RuntimeError("ClickHouse non pronto")

async def wait_for_postgres(dsn: str, retries: int = 30, interval: int = 2):
    for i in range(retries):
        try:
            conn = await asyncpg.connect(dsn=dsn)
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto (tentativo %d/%d)", i+1, retries)
            await asyncio.sleep(interval)
    raise RuntimeError("Postgres non pronto")

def create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=SSL_CAFILE)
    ctx.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)
    return ctx

async def consumer_loop():
    # --- readiness ---
    host, port = KAFKA_BROKER.split(":")
    # Kafka
    await asyncio.get_event_loop().run_in_executor(
        None, wait_for_broker, host, int(port)
    )
    logger.info("Kafka è pronto")
    # ClickHouse
    await wait_for_clickhouse()
    # Postgres
    pg_dsn = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    await wait_for_postgres(pg_dsn)

    # --- consumer setup ---
    ssl_ctx = create_ssl_context()
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        security_protocol="SSL",
        ssl_context=ssl_ctx,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    await consumer.start()

    # --- apri pool Postgres e client ClickHouse ---
    pg_pool = await asyncpg.create_pool(dsn=pg_dsn, min_size=1, max_size=5)
    ch = CHClient(
        host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE
    )

    try:
        async for msg in consumer:
            data = msg.value
            user_id   = data["user_id"]
            lat       = data["latitude"]
            lon       = data["longitude"]
            ts        = data["timestamp"]

            # 1) Trova il negozio più vicino in Postgres
            row = await pg_pool.fetchrow(
                """
                SELECT shop_id, shop_name,
                  ST_DistanceSphere(geom, ST_MakePoint($1, $2)) AS distance
                FROM shops
                ORDER BY geom <-> ST_MakePoint($1, $2)
                LIMIT 1
                """,
                lon, lat
            )
            if row:
                shop_id, shop_name, dist = (
                    row["shop_id"], row["shop_name"], row["distance"]
                )
            else:
                shop_id = None
                shop_name = ""
                dist = 0.0

            # 2) Inserisci in ClickHouse user_events
            event_id = int(datetime.now(timezone.utc).timestamp() * 1e6)
            ch.execute(
                """
                INSERT INTO user_events
                  (event_id, event_time, user_id,
                   latitude, longitude,
                   poi_range, poi_name, poi_info)
                VALUES
                """,
                [{
                    "event_id":   event_id,
                    "event_time": ts,
                    "user_id":    user_id,
                    "latitude":   lat,
                    "longitude":  lon,
                    "poi_range":  dist,
                    "poi_name":   shop_name,
                    "poi_info":   shop_name
                }]
            )

            logger.debug(
                "Evt %d: user=%d → shop=%s (%.1fm)",
                event_id, user_id, shop_name, dist
            )
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consumer_loop())
