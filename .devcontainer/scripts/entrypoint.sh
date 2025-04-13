#!/usr/bin/env bash
echo "Inizio configurazione: imposto ownership e permessi su /opt/airflow_home..."
chown -R airflow:airflow /opt/airflow_home
chmod -R 777 /opt/airflow_home
echo "Permessi configurati. Avvio di Airflow Scheduler come utente 'airflow'..."
exec su airflow -c 'exec airflow scheduler'
