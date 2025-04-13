#!/bin/bash
set -e
if [ ! -f "$AIRFLOW_HOME/airflow.cfg" ]; then
  echo "airflow.cfg non trovato. Inizializzazione del database Airflow..."
  python -m airflow db init
fi
exec python -m airflow "$@"
