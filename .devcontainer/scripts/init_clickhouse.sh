#!/bin/bash
set -e

echo "Working directory: $(pwd)"
echo "Files in directory: $(ls -l)"

echo "Attesa per essere sicuri che ClickHouse sia pronto..."
sleep 30

echo "Creazione della tabella users..."
docker exec -i clickhouse-server clickhouse-client <<EOF
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

echo "Creazione della tabella user_events..."
docker exec -i clickhouse-server clickhouse-client <<EOF
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
