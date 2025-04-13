#!/bin/bash
set -e

# Se il file airflow.cfg non esiste, inizializza il database Airflow
if [ ! -f "$AIRFLOW_HOME/airflow.cfg" ]; then
  echo "airflow.cfg non trovato. Inizializzazione del database Airflow..."
  airflow db init
fi

exec airflow "$@"
