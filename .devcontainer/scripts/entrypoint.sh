#!/usr/bin/env bash
set -e

echo "Inizio configurazione: imposto ownership e permessi su /opt/airflow_home..."
if chown -R airflow /opt/airflow_home; then
    echo "Ownership impostato correttamente."
else
    echo "Errore nell'impostazione dell'ownership." >&2
    exit 1
fi

if chmod -R 777 /opt/airflow_home; then
    echo "Permessi impostati correttamente."
else
    echo "Errore nell'impostazione dei permessi." >&2
    exit 1
fi

echo "Inizializzazione e upgrade del database..."
# Esegue airflow db init e, in ogni caso, airflow db upgrade per applicare tutte le migrazioni mancanti.
su airflow -c "airflow db init" || true
su airflow -c "airflow db upgrade"

echo "Attivo automaticamente il DAG etl_shops..."
su airflow -c "airflow dags unpause etl_shops" || echo "DAG etl_shops già attivo o errore nell'unpause."

echo "Avvio di Airflow Scheduler come utente 'airflow'..."
exec su airflow -c "airflow scheduler"
