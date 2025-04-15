from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from clickhouse_driver import Client
import psycopg2

from config import (
    CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE,
    POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NearYou Web App")

# Monta la cartella "static" (se in futuro decidi di usare file statici, ad esempio CSS/JS personalizzati)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inizializza il client ClickHouse
ch_client = Client(
    host=CLICKHOUSE_HOST,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    port=CLICKHOUSE_PORT,
    database=CLICKHOUSE_DATABASE
)

# Helper per Postgres: funzione per ottenere una connessione
def get_postgres_connection():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB
        )
        return conn
    except Exception as e:
        logger.error("Errore nella connessione a PostgreSQL: %s", e)
        raise

# Endpoint: recupera gli eventi degli utenti (ClickHouse)
@app.get("/user_events", response_class=JSONResponse)
def get_user_events(limit: int = 100):
    try:
        # Presupponiamo che la tabella user_events abbia le colonne: event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info
        query = f"SELECT * FROM user_events ORDER BY event_time DESC LIMIT {limit}"
        result = ch_client.execute(query)
        data = []
        for row in result:
            event = {
                "event_id": row[0],
                "event_time": row[1].isoformat() if hasattr(row[1], "isoformat") else row[1],
                "user_id": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "poi_range": row[5],
                "poi_name": row[6],
                "poi_info": row[7]
            }
            data.append(event)
        return data
    except Exception as e:
        logger.error("Errore nel recupero degli eventi: %s", e)
        raise HTTPException(status_code=500, detail="Errore interno del server")

# Endpoint: recupera i negozi (Postgres)
@app.get("/shops", response_class=JSONResponse)
def get_shops():
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        # Seleziona alcuni campi chiave, utilizza ST_AsText per il campo geometrico.
        cur.execute("SELECT shop_id, shop_name, address, category, ST_AsText(geom) FROM shops LIMIT 100;")
        rows = cur.fetchall()
        shops = []
        for row in rows:
            shop = {
                "shop_id": row[0],
                "shop_name": row[1],
                "address": row[2],
                "category": row[3],
                "geom": row[4]  # Formato: 'POINT(lon lat)'
            }
            shops.append(shop)
        cur.close()
        conn.close()
        return shops
    except Exception as e:
        logger.error("Errore nel recupero dei negozi: %s", e)
        raise HTTPException(status_code=500, detail="Errore interno del server")

# Endpoint: pagina principale con la mappa
@app.get("/", response_class=HTMLResponse)
def index():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>NearYou - Live Map</title>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
      <style>
        #map { height: 90vh; width: 100%; }
        body { font-family: Arial, sans-serif; }
      </style>
    </head>
    <body>
      <h1>NearYou - Live Map</h1>
      <div id="map"></div>
      <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
      <script>
      // Inizializza la mappa con una vista centrale
      var map = L.map('map').setView([45.45, 9.2], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '© OpenStreetMap'
      }).addTo(map);
      
      // Recupera gli eventi utente e posiziona i marker
      fetch('/user_events')
        .then(response => response.json())
        .then(data => {
            data.forEach(function(event) {
                if(event.latitude && event.longitude){
                    var marker = L.marker([event.latitude, event.longitude]).addTo(map);
                    var popupContent = "<b>User ID:</b> " + event.user_id + "<br/>" +
                                       "<b>Time:</b> " + event.event_time + "<br/>" +
                                       "<b>Info:</b> " + event.poi_name + " " + event.poi_info;
                    marker.bindPopup(popupContent);
                }
            });
        })
        .catch(error => console.error('Errore nel recupero degli eventi:', error));

      // Recupera i negozi e aggiungi marker (utilizza cerchi rossi)
      fetch('/shops')
        .then(response => response.json())
        .then(data => {
            data.forEach(function(shop) {
                // Converti la geometria in coordinate
                var regex = /POINT\\(([^ ]+) ([^\\)]+)\\)/;
                var match = regex.exec(shop.geom);
                if(match){
                    var lon = parseFloat(match[1]);
                    var lat = parseFloat(match[2]);
                    var circle = L.circleMarker([lat, lon], {color: 'red'}).addTo(map);
                    var popupContent = "<b>Shop:</b> " + shop.shop_name + "<br/>" +
                                       "<b>Category:</b> " + shop.category + "<br/>" +
                                       "<b>Address:</b> " + shop.address;
                    circle.bindPopup(popupContent);
                }
            });
        })
        .catch(error => console.error('Errore nel recupero dei negozi:', error));
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
