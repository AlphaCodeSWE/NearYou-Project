# dashboard-admin/backend/analytics/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .db import get_clickhouse_client, get_postgres_pool

# qui indichiamo dove sta l'endpoint /login (admin-auth)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://admin-auth:8002/login")

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)

async def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Se vuoi, qui puoi chiamare l'admin-auth per validare il JWT.
    Per ora accettiamo qualunque token non vuoto.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
        )
    return token

@router.get("/stats", summary="Conteggio utenti registrati")
async def stats(token: str = Depends(verify_token)):
    try:
        client = get_clickhouse_client()
        # COUNT(*) oppure COUNT()
        result = client.execute("SELECT count() FROM users")
        return {"user_count": result[0][0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {e}")

@router.get("/users", summary="Elenco utenti (fino a 100)")
async def list_users(token: str = Depends(verify_token)):
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
async def list_shops(token: str = Depends(verify_token)):
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
