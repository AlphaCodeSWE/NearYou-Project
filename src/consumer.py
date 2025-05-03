#!/usr/bin/env python3
import os
import asyncio
import json
import logging
from datetime import datetime
from dateutil import parser as date_parser  # pip install python-dateutil

import asyncpg
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client as CHClient

from logger_config import setup_logging
from configg import (
    KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
)
from utils import wait_for_broker, wait_for_clickhouse

logger = logging.getLogger(__name__)
setup_logging()

async def wait_for_postgres(host: str, port: int, retries: int = 30, interval: float = 2.0):
    for i in range(retries):
        try:
            conn = await asyncpg.connect(
                host=host, port=port,
                user=POSTGRES_USER, password=POSTGRES_PASSWORD,
                database=POSTGRES_DB
            )
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto, tentativo %d/%d", i+1, retries)
            await asyncio.sleep(interval)
    raise RuntimeError("Postgres non pronto")

async def consumer_loop():
    # Readiness checks
    host_k, port_k = KAFKA_BROKER.split(":")
    await asyncio.gather(
        wait_for_broker(host_k, int(port_k)),
        wait_for_clickhouse(),
        wait_for_postgres(POSTGRES_HOST, POSTGRES_PORT),
    )
    logger.info("Tutti i servizi sono pronti, avvio consumer")

    # Create ClickHouse client
    ch_client = CHClient(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DATABASE
    )

    # Create Postgres pool
    pg_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        min_size=1, max_size=5
    )

    # Kafka consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        security_protocol="SSL",
        ssl_cafile=None,  
        ssl_certfile=None,
        ssl_keyfile=None,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
    )
    await consumer.start()

    try:
        async for msg in consumer:
            try:
                # msg.value è bytes: decodifico e carico JSON
                record = json.loads(msg.value.decode("utf-8"))
                # parsing ISO timestamp -> datetime con tzinfo
                ts = date_parser.isoparse(record["timestamp"])

                uid       = record["user_id"]
                lat, lon  = record["latitude"], record["longitude"]
                # calcolo distanza al POI più vicino
                shop = await pg_pool.fetchrow(
                    """
                    SELECT shop_id, shop_name,
                           ST_Distance(
                             geom::geography,
                             ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                           ) AS dist_m
                    FROM shops
                    ORDER BY dist_m
                    LIMIT 1
                    """,
                    lon, lat
                )
                poi_range = shop["dist_m"]
                poi_name  = shop["shop_name"]

                # scrivo in ClickHouse
                ch_client.execute(
                    """
                    INSERT INTO user_events (
                        event_id, event_time, user_id,
                        latitude, longitude,
                        poi_range, poi_name, poi_info
                    ) VALUES
                    """,
                    [{
                        "event_id":     int(msg.offset),       # offset usato come chiave univoca
                        "event_time":   ts,
                        "user_id":      uid,
                        "latitude":     lat,
                        "longitude":    lon,
                        "poi_range":    poi_range,
                        "poi_name":     poi_name,
                        "poi_info":     "",                   # eventualmente dettagli extra
                    }]
                )

                logger.info(
                    "Elaborato msg offset=%d user=%d → poi %s a %.1fm",
                    msg.offset, uid, poi_name, poi_range
                )

            except Exception as e:
                logger.error("Errore elaborazione messaggio %s: %s", msg, e, exc_info=True)

    finally:
        await consumer.stop()
        await pg_pool.close()

if __name__ == "__main__":
    asyncio.run(consumer_loop())
