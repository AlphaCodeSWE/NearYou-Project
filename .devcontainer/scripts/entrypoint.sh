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

echo "Controllo inizializzazione del database..."
if ! su airflow -c "airflow db check" > /dev/null 2>&1; then
    echo "Il database non è inizializzato: eseguo 'airflow db init' e 'airflow db upgrade'..."
    su airflow -c "airflow db init"
    su airflow -c "airflow db upgrade"
else
    echo "Il database è già inizializzato."
fi

echo "Avvio di Airflow Scheduler come utente 'airflow'..."
exec su airflow -c "airflow scheduler"
