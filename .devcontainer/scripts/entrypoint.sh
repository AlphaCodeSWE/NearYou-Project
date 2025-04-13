#!/bin/bash
set -e

if [ ! -f "$AIRFLOW_HOME/airflow.cfg" ]; then
  echo "airflow.cfg non trovato. Inizializzazione del database Airflow..."
  airflow db init
fi

# Richiamo dell'entrypoint ufficiale per configurare l'ambiente di Airflow
exec /entrypoint "$@"
