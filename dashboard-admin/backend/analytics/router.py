# dashboard-admin/backend/analytics/router.py

import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from db import get_clickhouse_client, get_postgres_pool
import jwt

# punto di ingresso per ottenere il token via /login su admin-auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://admin-auth:8002/login")

# dipendenza per validare il token
def verify_token(token: str = Depends(oauth2_scheme)):
    secret = os.getenv("JWT_SECRET")
    algo = os.getenv("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, secret, algorithms=[algo])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

router = APIRouter()

@router.get("/stats", summary="Conteggio utenti registrati")
async def stats(token=Depends(verify_token)):
    try:
        client = get_clickhouse_client()
        # in ClickHouse `count()` è equivalente a COUNT(*)
        result = client.execute("SELECT count() FROM users")
        return {"user_count": result[0][0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {e}")

@router.get("/users", summary="Elenco utenti (fino a 100)")
async def list_users(token=Depends(verify_token)):
    try:
        client = get_clickhouse_client()
        rows = client.execute("""
            SELECT user_id, full_name, email
            FROM users
            ORDER BY registration_time DESC
            LIMIT 100
        """)
        return [
            {"user_id": uid, "full_name": fn, "email": em}
            for uid, fn, em in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {e}")

@router.get("/shops", summary="Elenco negozi")
async def list_shops(token=Depends(verify_token)):
    try:
        pool = await get_postgres_pool()
        rows = await pool.fetch("""
            SELECT shop_id, shop_name, category
            FROM shops
            ORDER BY shop_name
        """)
        return [
            {"shop_id": r["shop_id"], "shop_name": r["shop_name"], "category": r["category"]}
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Postgres error: {e}")
