#!/usr/bin/env python3
import os
import asyncio
import logging
import ssl
import json
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient
import asyncpg

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, KAFKA_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    PG_DSN,
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT, CLICKHOUSE_DATABASE,
)
from utils import wait_for_broker, wait_for_postgres, wait_for_clickhouse

logger = logging.getLogger(__name__)
setup_logging()

async def consumer_loop():
    # readiness
    await asyncio.gather(
        wait_for_broker(*KAFKA_BROKER.split(":")),
        wait_for_postgres(),
        wait_for_clickhouse(),
    )

    # prepara SSLContext
    ssl_ctx = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_ctx.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)

    # inizializza consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_context=ssl_ctx,
        group_id=KAFKA_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    await consumer.start()

    # connessioni a DB
    pg_pool = await asyncpg.create_pool(dsn=PG_DSN)
    ch_client = CHClient(
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
            age       = data["age"]
            profession= data["profession"]
            interests = data["interests"]

            # 1) salva in Postgres (PostGIS)
            async with pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO gps_points (user_id, ts, geom)
                    VALUES ($1, $2, ST_SetSRID(ST_MakePoint($3, $4), 4326))
                    """,
                    user_id, ts, lon, lat
                )

            # 2) salva in ClickHouse
            ch_client.execute(
                """
                INSERT INTO gps_stream
                (user_id, timestamp, latitude, longitude, age, profession, interests)
                VALUES
                """,
                [{
                    "user_id": user_id,
                    "timestamp": ts,
                    "latitude": lat,
                    "longitude": lon,
                    "age": age,
                    "profession": profession,
                    "interests": interests,
                }]
            )

            logger.debug("Messaggio consumato e salvato: %s", data)

    finally:
        await consumer.stop()
        await pg_pool.close()

if __name__ == "__main__":
    asyncio.run(consumer_loop())
