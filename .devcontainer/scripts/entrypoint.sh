#!/usr/bin/env bash
set -e

echo "Inizio configurazione: imposto ownership e permessi su /opt/airflow_home (escludendo 'dags')..."

# Modifica ownership e permessi su tutte le directory/ file in /opt/airflow_home tranne la cartella 'dags'
find /opt/airflow_home -mindepth 1 -maxdepth 1 ! -name 'dags' -exec chown -R airflow {} +
find /opt/airflow_home -mindepth 1 -maxdepth 1 ! -name 'dags' -exec chmod -R 777 {} +

echo "Ownership e permessi impostati correttamente (esclusa la cartella 'dags')."

echo "Avvio di Airflow Scheduler come utente 'airflow'..."
exec su airflow -c "airflow scheduler"
