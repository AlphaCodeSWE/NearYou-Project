# appsota/superset_config.py

# Sorgenti dati
# ----------------
# Attenzione: qui NON ci mettiamo le credenziali in chiaro in produzione!
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset.db"

from superset.config import *  # mantiene il resto della configurazione di default

# Definizione dei database esterni
DATABASES = {
    "clickhouse_nearyou": {
        "ENGINE": "clickhouse_driver",
        "NAME": "nearyou",
        "USER": "default",
        "PASSWORD": "pwe@123@l@",
        "HOST": "clickhouse-server",
        "PORT": 8123,
        "SQLALCHEMY_URI": "clickhouse://default:pwe@123@l@@clickhouse-server:8123/nearyou",
    },
    "postgres_shops": {
        "ENGINE": "postgresql+psycopg2",
        "NAME": "near_you_shops",
        "USER": "nearuser",
        "PASSWORD": "nearypass",
        "HOST": "postgres-postgis",
        "PORT": 5432,
        "SQLALCHEMY_URI": "postgresql+psycopg2://nearuser:nearypass@postgres-postgis:5432/near_you_shops",
    },
}


SECRET_KEY =  "TOdtv2DU5QndrNhKajh7LbsBJTvOop6Dt7J+r46lh4q+AzJ3IWNg9h+c"