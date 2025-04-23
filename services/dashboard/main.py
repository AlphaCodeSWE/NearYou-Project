import os
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from clickhouse_driver import Client
from pydantic import BaseModel
from configg import (
    CLICKHOUSE_HOST, CLICKHOUSE_PORT,
    CLICKHOUSE_USER, CLICKHOUSE_PASSWORD,
    CLICKHOUSE_DATABASE
)

app = FastAPI(title="NearYou Dashboard")

# Monta la cartella 'frontend' per servire index.html
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# ClickHouse client
client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE
)

# Attendi che ClickHouse risponda
while True:
    try:
        client.execute("SELECT 1")
        break
    except Exception:
        time.sleep(2)

class Position(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    message: str | None

class PositionsResponse(BaseModel):
    positions: list[Position]

@app.get("/api/positions", response_model=PositionsResponse)
async def get_positions():
    query = """
    SELECT
      user_id,
      argMax(latitude, event_time)  AS latitude,
      argMax(longitude, event_time) AS longitude,
      argMax(poi_info, event_time)  AS message
    FROM user_events
    GROUP BY user_id
    LIMIT 20
    """
    rows = client.execute(query)
    return {"positions": [
        {"user_id": r[0], "latitude": r[1], "longitude": r[2], "message": r[3] or None}
        for r in rows
    ]}
