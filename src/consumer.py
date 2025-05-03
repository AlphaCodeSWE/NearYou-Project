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
from utils import wait_for_broker, wait_for_postgres, wait_for_clickhouse
from logger_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()

async def consumer_loop():
    # 1) Readiness checks
    host, port = KAFKA_BROKER.split(":")
    await wait_for_broker(host, int(port))
    logger.info("Kafka è pronto")

    await wait_for_postgres()
    logger.info("Postgres è pronto")

    await wait_for_clickhouse()
    logger.info("ClickHouse è pronto")

    # 2) Prepara SSL context per Kafka
    ssl_context = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_context.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)

    # 3) Istanzia il consumer Kafka
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

    # 4) Connetti ai database
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
        # 5) Consuma i messaggi in streaming
        async for msg in consumer:
            data = msg.value
            logger.debug("Ricevuto: %s", data)

            # --- Inserimento su Postgres ---
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

            # --- Inserimento su ClickHouse ---
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
        # 6) Pulizia
        await consumer.stop()
        await pg_pool.close()

if __name__ == "__main__":
    asyncio.run(consumer_loop())
