from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from .db import get_clickhouse_client, get_postgres_pool

router = APIRouter()

class Stat(BaseModel):
    metric: str
    value: float

@router.get("/stats", response_model=List[Stat])
async def stats(ch=Depends(get_clickhouse_client)):
    # numero di utenti distinti attivi nell’ultima ora
    result = ch.execute(
        "SELECT countDistinct(user_id) FROM user_events "
        "WHERE event_time > now() - INTERVAL 1 HOUR"
    )
    return [Stat(metric="active_users_last_hour", value=result[0][0])]

@router.get("/users")
async def list_users(ch=Depends(get_clickhouse_client)):
    rows = ch.execute("SELECT user_id, age, profession FROM users")
    return [{"user_id": u, "age": a, "profession": p} for u, a, p in rows]

@router.get("/map")
async def map_events(ch=Depends(get_clickhouse_client)):
    rows = ch.execute(
        "SELECT latitude, longitude, user_id "
        "FROM user_events "
        "WHERE event_time > now() - INTERVAL 1 MINUTE"
    )
    return [{"lat": lat, "lon": lon, "user_id": uid} for lat, lon, uid in rows]
