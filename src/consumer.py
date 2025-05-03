#!/usr/bin/env python3
import os
import asyncio
import logging
import json
import ssl

from datetime import datetime, timezone

import asyncpg
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient

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
logging.basicConfig(level=logging.INFO)


async def wait_for_clickhouse(retries: int = 30, interval: int = 2):
    for i in range(retries):
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
            logger.debug("ClickHouse non pronto (%d/%d)", i + 1, retries)
            await asyncio.sleep(interval)
    raise RuntimeError("ClickHouse non pronto")


async def wait_for_postgres(retries: int = 30, interval: int = 2):
    for i in range(retries):
        try:
            conn = await asyncpg.connect(
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
            )
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto (%d/%d)", i + 1, retries)
            await asyncio.sleep(interval)
    raise RuntimeError("Postgres non pronto")


async def consumer_loop():
    # 1) Readiness checks
    host, port = KAFKA_BROKER.split(":")
    await asyncio.get_event_loop().run_in_executor(
        None, wait_for_broker, host, int(port)
    )
    logger.info("Kafka è pronto")

    await wait_for_postgres()
    await wait_for_clickhouse()

    # 2) SSL context per Kafka
    ssl_context = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_context.load_cert_chain(certfile=SSL_CERTFILE, keyfile=SSL_KEYFILE)

    # 3) Consumer Kafka
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_context=ssl_context,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
    )
    await consumer.start()

    # 4) Connessioni DB
    ch_client = CHClient(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE,
    )
    pg_pool = await asyncpg.create_pool(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        min_size=1,
        max_size=10,
    )

    try:
        async for msg in consumer:
            try:
                # decode e parse JSON
                payload = json.loads(msg.value.decode("utf-8"))
                # parse ISO8601 timestamp in UTC
                ts = datetime.fromisoformat(payload["timestamp"])
                if ts.tzinfo is None:
                    # in caso manchi tzinfo, forziamo UTC
                    ts = ts.replace(tzinfo=timezone.utc)

                # 1) Cerco il POI più vicino in Postgres
                row = await pg_pool.fetchrow(
                    """
                    SELECT
                      shop_id,
                      ST_Distance(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                      ) AS dist_m
                    FROM shops
                    ORDER BY dist_m
                    LIMIT 1
                    """,
                    payload["longitude"],
                    payload["latitude"],
                )
                shop_id = row["shop_id"]
                dist = row["dist_m"]

                # 2) Inserisco l'evento in ClickHouse
                # user_events(event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info)
                ch_client.execute(
                    """
                    INSERT INTO user_events (
                      event_id,
                      event_time,
                      user_id,
                      latitude,
                      longitude,
                      poi_range,
                      poi_name,
                      poi_info
                    ) VALUES
                    """,
                    [
                        {
                            "event_id": msg.offset,
                            "event_time": ts,
                            "user_id": payload["user_id"],
                            "latitude": payload["latitude"],
                            "longitude": payload["longitude"],
                            "poi_range": dist,
                            "poi_name": str(shop_id),
                            "poi_info": "",
                        }
                    ],
                )

                logger.debug(
                    "Elaborato msg %s → user %d, nearest shop %s (%.1fm)",
                    msg.offset,
                    payload["user_id"],
                    shop_id,
                    dist,
                )

            except Exception as e:
                logger.error("Errore elaborazione messaggio %s: %s", msg, e)

    finally:
        await consumer.stop()
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(consumer_loop())
