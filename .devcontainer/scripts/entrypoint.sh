#!/usr/bin/env bash
set -e

echo "Controllo inizializzazione del database..."
if ! airflow db check > /dev/null 2>&1; then
    echo "Database non inizializzato: avvio 'airflow db init' e 'airflow db upgrade'..."
    airflow db init
    airflow db upgrade
else
    echo "Database già inizializzato."
fi

echo "Inizio configurazione: imposto ownership e permessi su /opt/airflow_home (escludendo 'dags')..."
# Cambia ownership e permessi su tutte le directory in /opt/airflow_home, tranne 'dags'
find /opt/airflow_home -mindepth 1 -maxdepth 1 ! -name 'dags' -exec chown -R airflow {} +
find /opt/airflow_home -mindepth 1 -maxdepth 1 ! -name 'dags' -exec chmod -R 777 {} +

echo "Avvio di Airflow Scheduler come utente 'airflow'..."
exec su airflow -c "airflow scheduler"
