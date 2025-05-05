from fastapi import APIRouter, Depends, HTTPException
from db import get_clickhouse_client, get_postgres_pool
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

router = APIRouter()

@router.get("/stats")
async def stats(token: str = Depends(oauth2_scheme)):
    # dummy example: conta utenti in ClickHouse
    client = get_clickhouse_client()
    res = client.execute("SELECT count(*) FROM users")
    return {"user_count": res[0][0]}

@router.get("/shops")
async def shops(token: str = Depends(oauth2_scheme)):
    pg = await get_postgres_pool()
    rows = await pg.fetch("SELECT shop_id, shop_name, category FROM shops")
    return [dict(r) for r in rows]
