#!/bin/bash
set -e

# Imposta i permessi di lettura, scrittura ed esecuzione per AIRFLOW_HOME
chmod -R 777 "${AIRFLOW_HOME}"

# Se non esiste il file di configurazione, inizializza il database Airflow
if [ ! -f "${AIRFLOW_HOME}/airflow.cfg" ]; then
  echo "airflow.cfg non trovato. Inizializzazione del database Airflow..."
  airflow db init
fi

exec airflow "$@"
