import os
import sys
import time

# 1) Aggiungi src/ al PYTHONPATH per importare configg.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from clickhouse_driver import Client
from pydantic import BaseModel

# 2) Importa direttamente le costanti da src/configg.py
from configg import (
    CLICKHOUSE_HOST,
    CLICKHOUSE_PORT,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_DATABASE
)

# 3) Crea l’app FastAPI e monta il frontend statico
app = FastAPI(title="NearYou Dashboard")
static_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# 4) Inizializza ClickHouse client e attendi che sia pronto
client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE
)
while True:
    try:
        client.execute("SELECT 1")
        break
    except:
        time.sleep(2)

# 5) Modelli Pydantic per la risposta
class Position(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    message: str | None

class PositionsResponse(BaseModel):
    positions: list[Position]

# 6) Endpoint REST per le posizioni
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
    return {
        "positions": [
            {
                "user_id": r[0],
                "latitude": r[1],
                "longitude": r[2],
                "message": r[3] or None
            }
            for r in rows
        ]
    }
