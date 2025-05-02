# services/dashboard/main_user.py

import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles         # <- corretto
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from clickhouse_driver import Client

from .auth import authenticate_user, create_access_token, get_current_user, oauth2_scheme

app = FastAPI(title="NearYou User Dashboard")

# Monta la cartella frontend_user su /static_user
static_dir = os.path.join(os.path.dirname(__file__), "frontend_user")
app.mount("/static_user",
          StaticFiles(directory=static_dir),
          name="static_user")

# Client ClickHouse per posizioni
ch = Client(
    host=os.getenv("CLICKHOUSE_HOST", "clickhouse-server"),
    port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
    user=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    database=os.getenv("CLICKHOUSE_DATABASE", "nearyou"),
)

@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Credenziali errate")
    token = create_access_token({"user_id": user["user_id"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/dashboard/user", response_class=HTMLResponse)
async def user_dashboard(token: str = Depends(oauth2_scheme)):
    # Token già validato da oauth2_scheme
    html_path = os.path.join(static_dir, "index_user.html")
    return HTMLResponse(open(html_path, encoding="utf8").read())

@app.get("/api/user/positions")
async def user_positions(current: dict = Depends(get_current_user)):
    uid = current["user_id"]
    since = int((datetime.utcnow() - timedelta(minutes=10)).timestamp())
    query = f"""
        SELECT
          user_id,
          argMax(latitude,  event_time) AS lat,
          argMax(longitude, event_time) AS lon,
          argMax(poi_info,   event_time) AS msg
        FROM user_events
        WHERE event_time >= toDateTime({since})
          AND user_id = {uid}
        GROUP BY user_id
        LIMIT 1
    """
    rows = ch.execute(query)
    if not rows:
        return {"positions": []}
    r = rows[0]
    return {"positions": [
        {"user_id": r[0], "latitude": r[1], "longitude": r[2], "message": r[3] or None}
    ]}
