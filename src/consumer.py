#!/usr/bin/env python3
import os
import asyncio
import logging
import ssl
import json
from datetime import datetime

import asyncpg
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE,
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT, CLICKHOUSE_DATABASE,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER,
    POSTGRES_PASSWORD, POSTGRES_DB,
)
from utils import wait_for_broker

logger = logging.getLogger(__name__)
setup_logging()


async def wait_for_kafka():
    host, port = KAFKA_BROKER.split(":")
    await asyncio.get_event_loop().run_in_executor(
        None, wait_for_broker, host, int(port)
    )
    logger.info("Kafka è pronto")


async def wait_for_postgres(retries: int = 30, interval: int = 2):
    for i in range(retries):
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
            logger.debug("Postgres non pronto (tentativo %d/%d)", i+1, retries)
            await asyncio.sleep(interval)
    raise RuntimeError("Postgres non pronto")


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


async def consumer_loop():
    # 1) readiness checks
    await asyncio.gather(
        wait_for_kafka(),
        wait_for_postgres(),
        wait_for_clickhouse(),
    )

    # 2) prepara SSLContext per Kafka
    ssl_ctx = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_ctx.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)

    # 3) inizializza Kafka consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_context=ssl_ctx,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    await consumer.start()

    # 4) apri pool Postgres e client ClickHouse
    pg_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        user=POSTGRES_USER, password=POSTGRES_PASSWORD,
        database=POSTGRES_DB, min_size=1, max_size=5
    )
    ch = CHClient(
        host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE
    )

    try:
        async for msg in consumer:
            record = msg.value  # ora un dict
            try:
                # 5) parse timestamp ISO
                event_time = datetime.fromisoformat(record["timestamp"])
            except Exception as e:
                logger.error("Problema nel parse della timestamp %r: %s", record.get("timestamp"), e)
                continue

            lat = record["latitude"]
            lon = record["longitude"]
            user_id = record["user_id"]

            # 6) trova il negozio più vicino in Postgres (SRID 4326)
            try:
                pg_query = """
                    SELECT shop_id, shop_name, address, category,
                        ST_Distance(
                            geom,
                            ST_SetSRID(ST_MakePoint($1, $2), 4326)
                        ) AS dist
                    FROM shops
                    ORDER BY dist
                    LIMIT 1
                """
                row = await pg_pool.fetchrow(pg_query, lon, lat)
                if row:
                    poi_range = row["dist"]
                    poi_name  = row["shop_name"]
                    poi_info  = row["category"]
                else:
                    poi_range = None
                    poi_name  = ""
                    poi_info  = ""
            except Exception as e:
                logger.error("Errore query Postgres per record %s: %s", record, e)
                poi_range = None
                poi_name  = ""
                poi_info  = ""

            # 7) inserisci in ClickHouse
            try:
                ch.execute(
                    "INSERT INTO user_events "
                    "(event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info) "
                    "VALUES",
                    [
                        (
                            msg.offset,
                            event_time,
                            user_id,
                            lat,
                            lon,
                            poi_range or 0.0,
                            poi_name,
                            poi_info
                        )
                    ]
                )
                logger.debug("Evento scrittura CH: offset=%d user=%d poi=%s (d=%.2f)",
                             msg.offset, user_id, poi_name, poi_range or 0.0)
            except Exception as e:
                logger.error("Errore inserimento ClickHouse per record %s: %s", record, e)

    finally:
        # pulizia risorse
        await consumer.stop()
        await pg_pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(consumer_loop())
    except KeyboardInterrupt:
        logger.info("Consumer interrotto manualmente")
