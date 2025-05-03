#!/usr/bin/env python3
import asyncio
import json
import logging
import ssl

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


async def wait_for_clickhouse():
    for attempt in range(30):
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
            logger.debug("ClickHouse non pronto (tentativo %d/30)", attempt + 1)
            await asyncio.sleep(2)
    raise RuntimeError("ClickHouse non pronto")


async def wait_for_postgres():
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
            )
            await conn.close()
            logger.info("Postgres è pronto")
            return
        except Exception:
            logger.debug("Postgres non pronto (tentativo %d/30)", attempt + 1)
            await asyncio.sleep(2)
    raise RuntimeError("Postgres non pronto")


async def consumer_loop():
    # 1) Controlli di readiness
    host, port = KAFKA_BROKER.split(":")
    await asyncio.gather(
        asyncio.get_event_loop().run_in_executor(None, wait_for_broker, host, int(port)),
        wait_for_postgres(),
        wait_for_clickhouse(),
    )
    logger.info("Kafka, Postgres e ClickHouse sono pronti")

    # 2) Crea contesto SSL per Kafka
    ssl_context = ssl.create_default_context(cafile=SSL_CAFILE)
    ssl_context.load_cert_chain(SSL_CERTFILE, SSL_KEYFILE)

    # 3) Inizializza consumer Kafka
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        security_protocol="SSL",
        ssl_context=ssl_context,
        auto_offset_reset="latest",
    )
    await consumer.start()

    # 4) Pool Postgres e client ClickHouse
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

    event_id = 0

    try:
        async for msg in consumer:
            try:
                # Decodifica il messaggio Kafka
                data = json.loads(msg.value)
                user_id = data["user_id"]
                lat = data["latitude"]
                lon = data["longitude"]
                timestamp = data["timestamp"]

                # 1) Trova il negozio più vicino in Postgres
                row = await pg_pool.fetchrow(
                    """
                    SELECT
                        shop_id,
                        shop_name,
                        ST_DistanceSphere(
                            geom,
                            ST_SetSRID(ST_MakePoint($1, $2), 4326)
                        ) AS poi_range
                    FROM shops
                    ORDER BY geom <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)
                    LIMIT 1
                    """,
                    lon, lat,
                )
                if row:
                    shop_name = row["shop_name"]
                    poi_range = row["poi_range"]
                else:
                    shop_name = ""
                    poi_range = None

                # 2) Inserisci in ClickHouse nella tabella user_events
                event_id += 1
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
                        (
                            event_id,
                            timestamp,
                            user_id,
                            lat,
                            lon,
                            poi_range,
                            shop_name,
                            ""  # qui puoi mettere ulteriori informazioni su poi_info
                        )
                    ],
                )
                logger.info(
                    "Evento %d salvato: user=%s shop=%s distanza=%.2f",
                    event_id, user_id, shop_name, poi_range or 0.0,
                )

            except Exception as exc:
                logger.error("Errore elaborazione messaggio %s: %s", msg, exc)
    finally:
        await consumer.stop()


def main():
    asyncio.run(consumer_loop())


if __name__ == "__main__":
    main()
