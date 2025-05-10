#!/bin/bash
set -e

echo "Pulizia metadati Kafka per evitare problemi di riavvio..."

# Directory dove Kafka salva i dati
KAFKA_DATA_DIR="/bitnami/kafka/data"

# Rimuovi solo i file che causano problemi con i riavvii
if [ -d "$KAFKA_DATA_DIR" ]; then
    echo "Pulizia meta.properties in $KAFKA_DATA_DIR"
    find "$KAFKA_DATA_DIR" -name "meta.properties" -type f -delete 2>/dev/null || true
    
    # Opzionale: rimuovi anche altri checkpoint se necessario
    # find "$KAFKA_DATA_DIR" -name "*-checkpoint" -type f -delete 2>/dev/null || true
fi

echo "Metadati puliti. Avvio Kafka normale..."

# Esegui il comando di entrypoint originale di Bitnami
exec /opt/bitnami/scripts/kafka/entrypoint.sh /opt/bitnami/scripts/kafka/run.sh