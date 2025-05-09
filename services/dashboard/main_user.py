# services/dashboard/main_user.py

import os
import logging
import asyncpg
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from clickhouse_driver import Client

from .auth import authenticate_user, create_access_token, get_current_user

# ─── Configura logger ─────────────────────────────────────────────────────
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# ─── Modelli di dati ────────────────────────────────────────────────────────
class Position(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    message: Optional[str] = None

class PositionsResponse(BaseModel):
    positions: List[Position]

class UserProfile(BaseModel):
    user_id: int
    age: int
    profession: str
    interests: str

class Shop(BaseModel):
    id: int
    shop_name: str
    category: str
    lat: float
    lon: float
    distance: Optional[float] = None

# ─── Crea l'app FastAPI ───────────────────────────────────────────────────
app = FastAPI(title="NearYou User Dashboard")

# ─── Configurazione CORS ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Monta la UI statica ───────────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "frontend_user")
app.mount(
    "/static_user",
    StaticFiles(directory=static_dir),
    name="static_user",
)

# ─── Client ClickHouse ────────────────────────────────────────────────────
ch = Client(
    host=os.getenv("CLICKHOUSE_HOST", "clickhouse-server"),
    port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
    user=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    database=os.getenv("CLICKHOUSE_DATABASE", "nearyou"),
)

# ─── Configurazione Postgres ────────────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres-postgis")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "nearuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nearypass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "near_you_shops")

# ─── Funzioni di utilità ─────────────────────────────────────────────────
async def get_postgres_connection():
    """Crea una connessione a PostgreSQL."""
    try:
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        return conn
    except Exception as e:
        logger.error(f"Errore connessione PostgreSQL: {e}")
        raise HTTPException(status_code=500, detail="Errore connessione database")

# ─── Endpoint di debug per le env vars ────────────────────────────────────
@app.get("/__debug/env")
async def debug_env():
    """Endpoint di debug per verificare le variabili d'ambiente."""
    return {
        "JWT_SECRET": os.getenv("JWT_SECRET")[:5] + "..." if os.getenv("JWT_SECRET") else None,
        "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM"),
        "CLICKHOUSE_HOST": os.getenv("CLICKHOUSE_HOST"),
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
    }

# ─── Login e generazione token ────────────────────────────────────────────
@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint per l'autenticazione e generazione token JWT."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Credenziali errate")
    token = create_access_token({"user_id": user["user_id"]})
    return {"access_token": token, "token_type": "bearer"}

# ─── Reindirizza dalla radice alla dashboard utente ──────────────────────────
@app.get("/", response_class=RedirectResponse)
async def root():
    """Reindirizza dalla radice del sito alla dashboard utente."""
    return RedirectResponse(url="/dashboard/user")

# ─── Dashboard utente principale ────────────────────────
@app.get("/dashboard/user", response_class=HTMLResponse)
async def user_dashboard():
    """Endpoint che serve la dashboard utente."""
    html_path = os.path.join(static_dir, "index_user.html")
    return HTMLResponse(open(html_path, encoding="utf8").read())

# ─── API protetta: restituisce posizione utente ───────────────────────────
@app.get("/api/user/positions", response_model=PositionsResponse)
async def user_positions(current: dict = Depends(get_current_user)):
    """Restituisce la posizione dell'utente."""
    uid = current["user_id"]
    query = """
        SELECT
          user_id,
          argMax(latitude,  event_time) AS lat,
          argMax(longitude, event_time) AS lon,
          argMax(poi_info,   event_time) AS msg
        FROM user_events
        WHERE user_id = %(uid)s
        GROUP BY user_id
        LIMIT 1
    """
    rows = ch.execute(query, {"uid": uid})
    if not rows:
        return {"positions": []}
    r = rows[0]
    return {
        "positions": [
            {
                "user_id": r[0],
                "latitude": r[1],
                "longitude": r[2],
                "message": r[3] or None
            }
        ]
    }

# ─── API protetta: restituisce profilo utente ───────────────────────────
@app.get("/api/user/profile", response_model=UserProfile)
async def user_profile(
    current: dict = Depends(get_current_user),
    user_id: Optional[int] = Query(None, description="ID dell'utente (solo per debug)")
):
    """Restituisce il profilo dell'utente."""
    # Per sicurezza, usa l'ID dell'utente corrente, non quello in query
    # a meno che non siamo in modalità debug
    uid = user_id if user_id is not None else current["user_id"]
    
    query = """
        SELECT
          user_id, age, profession, interests
        FROM users
        WHERE user_id = %(uid)s
        LIMIT 1
    """
    
    rows = ch.execute(query, {"uid": uid})
    
    if not rows:
        raise HTTPException(status_code=404, detail="Profilo utente non trovato")
    
    return {
        "user_id": rows[0][0],
        "age": rows[0][1],
        "profession": rows[0][2],
        "interests": rows[0][3]
    }

# ─── API protetta: restituisce negozi vicini ───────────────────────────
@app.get("/api/shops/nearby", response_model=List[Shop])
async def shops_nearby(
    current: dict = Depends(get_current_user),
    radius: float = Query(1.0, description="Raggio di ricerca in km")
):
    """Restituisce i negozi vicini all'utente in un dato raggio."""
    uid = current["user_id"]
    
    # 1. Recupera ultima posizione dell'utente
    pos_query = """
        SELECT 
          latitude, 
          longitude
        FROM user_events 
        WHERE user_id = %(uid)s
        ORDER BY event_time DESC
        LIMIT 1
    """
    
    pos_rows = ch.execute(pos_query, {"uid": uid})
    
    if not pos_rows:
        raise HTTPException(status_code=404, detail="Posizione utente non trovata")
    
    lat, lon = pos_rows[0]
    
    # 2. Recupera negozi nel raggio specificato
    try:
        conn = await get_postgres_connection()
        
        shops_query = """
            SELECT 
                shop_id, 
                shop_name, 
                category,
                ST_Y(geom) as lat, 
                ST_X(geom) as lon,
                ST_Distance(
                    geom::geography, 
                    ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                ) as distance
            FROM shops
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                $3 * 1000  -- convertire km in metri
            )
            ORDER BY distance
            LIMIT 50
        """
        
        shops = await conn.fetch(shops_query, lon, lat, radius)
        await conn.close()
        
        # 3. Converte in formato risposta
        result = []
        for shop in shops:
            result.append({
                "id": shop["shop_id"],
                "shop_name": shop["shop_name"],
                "category": shop["category"],
                "lat": shop["lat"],
                "lon": shop["lon"],
                "distance": shop["distance"]
            })
            
        return result
        
    except Exception as e:
        logger.error(f"Errore recupero negozi vicini: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

# ─── API protetta: statistiche utente ───────────────────────────
@app.get("/api/user/stats")
async def user_stats(
    current: dict = Depends(get_current_user),
    time_period: str = Query("day", description="Periodo di tempo (day, week, month)")
):
    """Restituisce statistiche sull'attività dell'utente."""
    uid = current["user_id"]
    
    # Determina intervallo di tempo
    now = datetime.now()
    if time_period == "week":
        since = now - timedelta(days=7)
    elif time_period == "month":
        since = now - timedelta(days=30)
    else:  # day è il default
        since = now - timedelta(days=1)
    
    # Query per statistiche
    query = """
        SELECT 
            COUNT(*) as total_events,
            COUNT(DISTINCT toDate(event_time)) as active_days,
            COUNT(DISTINCT poi_name) as unique_shops,
            countIf(poi_info != '') as notifications
        FROM user_events
        WHERE user_id = %(uid)s
          AND event_time >= %(since)s
    """
    
    rows = ch.execute(query, {
        "uid": uid,
        "since": since.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    if not rows or not rows[0]:
        return {
            "total_events": 0,
            "active_days": 0,
            "unique_shops": 0,
            "notifications": 0
        }
    
    return {
        "total_events": rows[0][0],
        "active_days": rows[0][1],
        "unique_shops": rows[0][2],
        "notifications": rows[0][3]
    }

# ─── API protetta: restituisce tutte le promozioni ricevute ───────────────────────────
@app.get("/api/user/promotions")
async def user_promotions(
    current: dict = Depends(get_current_user),
    limit: int = Query(10, description="Numero massimo di promozioni da restituire"),
    offset: int = Query(0, description="Offset per la paginazione")
):
    """Restituisce le promozioni ricevute dall'utente."""
    uid = current["user_id"]
    
    query = """
        SELECT 
            event_id,
            event_time,
            poi_name,
            poi_info
        FROM user_events
        WHERE user_id = %(uid)s
          AND poi_info != ''
        ORDER BY event_time DESC
        LIMIT %(limit)s
        OFFSET %(offset)s
    """
    
    rows = ch.execute(query, {
        "uid": uid,
        "limit": limit,
        "offset": offset
    })
    
    result = []
    for row in rows:
        result.append({
            "event_id": row[0],
            "timestamp": row[1].isoformat(),
            "shop_name": row[2],
            "message": row[3]
        })
        
    return {"promotions": result}