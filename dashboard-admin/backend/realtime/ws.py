import os
import jwt
import asyncio
from fastapi import FastAPI, WebSocket, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from deps import connect_consumer, disconnect_consumer, consumer
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
bearer = HTTPBearer()

JWT_SECRET    = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

@app.on_event("startup")
async def on_startup():
    await connect_consumer()

@app.on_event("shutdown")
async def on_shutdown():
    await disconnect_consumer()

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: HTTPAuthorizationCredentials = Depends(bearer)
):
    # valida JWT
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    # invia in push ogni messaggio Kafka come Feature GeoJSON
    try:
        async for msg in consumer:  
            data = msg.value
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [data["longitude"], data["latitude"]],
                },
                "properties": {
                    k: v for k, v in data.items() if k not in ("latitude", "longitude")
                }
            }
            await websocket.send_json(feature)
    except Exception:
        await websocket.close()
