#!/usr/bin/env python3
import asyncio
import logging
import ssl

from aiokafka import AIOKafkaConsumer
import asyncpg
from clickhouse_driver import Client as CHClient

from configg import (
    KAFKA_BROKER,
    KAFKA_TOPIC,
    CONSUMER_GROUP,
    SSL_CAFILE,
    SSL_CERTFILE,
    SSL_KEYFILE,
    POSTGRES_HOST,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
    POSTGRES_PORT,
    CLICKHOUSE_HOST,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_DATABASE,
    CLICKHOUSE_PORT,
)
from utils import wait_for_broker
from logger_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()


async def wait_for_postgres(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    interval: float = 2.0,
    max_retries: int = 30,
):
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(
                host=host, port=port, user=user, password=password, database=database
            )
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto (tentativo %d/%d)", i + 1, max_retries)
            await asyncio.sleep(interval)
    raise RuntimeError("Postgres non pronto dopo troppe prove")


async def wait_for_clickhouse(
    interval: float = 2.0, max_retries: int = 30
):
    for i in range(max_retries):
        try:
            client = CHClient(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                user=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DATABASE,
            )
            client.execute("SELECT 1")
            logger.info("ClickHouse è pronto")
            return
        except Exception:
            logger.debug("ClickHouse non pronto (tentativo %d/%d)", i + 1, max_retries)
            await asyncio.sleep(interval)
    raise RuntimeError("ClickHouse non pronto dopo troppe prove")


async def consumer_loop():
    # 1) readiness Kafka
    host, port = KAFKA_BROKER.split(":")
    await wait_for_broker(host, int(port))
    logger.info("Kafka è pronto")

    # 2) readiness Postgres e ClickHouse
    await wait_for_postgres(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
    )
    await wait_for_clickhouse()

    # 3) SSL context per Kafka
    ssl_context = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_context.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)

    # 4) Kafka consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_context=ssl_context,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await consumer.start()

    # 5) Connessioni a DB
    pg_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
    )
    ch_client = CHClient(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE,
    )

    try:
        # 6) Loop di consumo
        async for msg in consumer:
            data = msg.value
            logger.debug("Ricevuto: %s", data)

            # Inserimento in Postgres
            await pg_pool.execute(
                """
                INSERT INTO gps_events
                  (user_id, latitude, longitude, timestamp, age, profession, interests)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                data["user_id"],
                data["latitude"],
                data["longitude"],
                data["timestamp"],
                data["age"],
                data["profession"],
                data["interests"],
            )

            # Inserimento in ClickHouse
            ch_client.execute(
                """
                INSERT INTO gps_events
                  (user_id, latitude, longitude, timestamp, age, profession, interests)
                VALUES
                """,
                [(
                    data["user_id"],
                    data["latitude"],
                    data["longitude"],
                    data["timestamp"],
                    data["age"],
                    data["profession"],
                    data["interests"],
                )]
            )

    finally:
        await consumer.stop()
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(consumer_loop())
