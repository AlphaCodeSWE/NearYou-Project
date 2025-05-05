import os
import asyncpg
from clickhouse_driver import Client

_CH_CLIENT = None
async def get_clickhouse_client():
    global _CH_CLIENT
    if _CH_CLIENT is None:
        _CH_CLIENT = Client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT")),
            user=os.getenv("CLICKHOUSE_USER"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
        )
    return _CH_CLIENT


_PG_POOL = None
async def get_postgres_pool():
    global _PG_POOL
    if _PG_POOL is None:
        _PG_POOL = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
        )
    return _PG_POOL
