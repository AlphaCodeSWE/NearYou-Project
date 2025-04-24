import os, sys, time
from datetime import datetime, timedelta

# 1 — rende importabile src/configg.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC  = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from clickhouse_driver import Client
from pydantic import BaseModel
from configg import (
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
)

# 2 — FastAPI + frontend statico
app = FastAPI(title="NearYou Dashboard")
static_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/",   StaticFiles(directory=static_dir, html=True), name="static")

# 3 — ClickHouse client (attesa readiness)
client = Client(
    host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)
while True:
    try: client.execute("SELECT 1"); break
    except: time.sleep(2)

# 4 — Pydantic models
class Position(BaseModel):
    user_id:   int
    latitude:  float
    longitude: float
    message:   str | None

class PositionsResponse(BaseModel):
    positions: list[Position]

# 5 — API positions (ultimi 10 min, max 50 record)
@app.get("/api/positions", response_model=PositionsResponse)
async def get_positions(minutes: int = 10, limit: int = 50):
    since = int((datetime.utcnow() - timedelta(minutes=minutes)).timestamp())
    query = f"""
        SELECT
          user_id,
          argMax(latitude,  event_time) AS lat,
          argMax(longitude, event_time) AS lon,
          argMax(poi_info,  event_time) AS msg
        FROM user_events
        WHERE event_time >= toDateTime({since})
        GROUP BY user_id
        ORDER BY max(event_time) DESC
        LIMIT {limit}
    """
    rows = client.execute(query)
    return {"positions":[
        {"user_id":r[0],"latitude":r[1],"longitude":r[2],"message":r[3] or None}
        for r in rows
    ]}
