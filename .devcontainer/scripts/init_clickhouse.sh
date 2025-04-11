#!/bin/bash
set -e

echo "--- Inizio script di inizializzazione ---"
echo "Working directory: $(pwd)"
echo "Elenco dei file nella directory:"
ls -l

echo "Attesa 60 secondi affinché ClickHouse sia pronto..."
sleep 60

# Creazione del database se non esiste
echo "Creazione del database 'nearyou' (se non esiste già)..."
docker exec -i clickhouse-server clickhouse-client <<EOF
CREATE DATABASE IF NOT EXISTS nearyou;
EOF

# Creazione della tabella users all'interno del database 'nearyou'
echo "Creazione della tabella users..."
docker exec -i clickhouse-server clickhouse-client <<EOF
USE nearyou;
CREATE TABLE IF NOT EXISTS users (
    user_id           UInt64,
    username          String,
    full_name         String,
    email             String,
    phone_number      String,
    password          String,
    user_type         String,
    gender            String,
    age               UInt32,
    profession        String,
    interests         String,
    country           String,
    city              String,
    registration_time DateTime
) ENGINE = MergeTree()
ORDER BY user_id;
EOF

# Creazione della tabella user_events all'interno del database 'nearyou'
echo "Creazione della tabella user_events..."
docker exec -i clickhouse-server clickhouse-client <<EOF
USE nearyou;
CREATE TABLE IF NOT EXISTS user_events (
    event_id   UInt64,
    event_time DateTime,
    user_id    UInt64,
    latitude   Float64,
    longitude  Float64,
    poi_range  Float64,
    poi_name   String,
    poi_info   String
) ENGINE = MergeTree()
ORDER BY event_id;
EOF

echo "Inizializzazione di ClickHouse completata."
