#!/usr/bin/env python3
import json
import os
import subprocess

def read_json_file(file_path):
    """Legge un file JSON e ritorna il suo contenuto."""
    with open(file_path, 'r') as f:
        return json.load(f)

# Crea una dashboard completa invece di usare sostituzioni
def create_dashboard():
    # Directory di lavoro
    base_dir = "/workspace/NearYou-Project"
    panels_dir = os.path.join(base_dir, "grafana/provisioning/dashboards/panels")
    
    # Crea la struttura base della dashboard
    dashboard = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [],
        "refresh": "5s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["nearyou", "tracking", "shops"],
        "templating": {"list": []},
        "time": {"from": "now-24h", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
        },
        "timezone": "",
        "title": "NearYou - Analisi Utenti e Negozi",
        "uid": "nearyou-dashboard",
        "version": 1,
        "weekStart": ""
    }
    
    # Carica ciascun pannello e aggiungilo alla dashboard
    panel_files = [
        "stat_users.json",
        "stat_event.json",
        "stat_shops.json",
        "chart_events_per_hour.json",
        "top_10_shops.json",
        "map_user_routes.json",
        "map_shops.json"
    ]
    
    for filename in panel_files:
        try:
            file_path = os.path.join(panels_dir, filename)
            panel = read_json_file(file_path)
            dashboard["panels"].append(panel)
            print(f"Aggiunto pannello da {filename}")
        except Exception as e:
            print(f"Errore nel caricamento del pannello {filename}: {e}")
    
    # Carica le variabili di template
    template_files = [
        "template_age.json",
        "template_profession.json",
        "template_interests.json",
        "template_filters.json",
        "template_datasources.json"
    ]
    
    for filename in template_files:
        try:
            file_path = os.path.join(panels_dir, filename)
            if filename == "template_filters.json" or filename == "template_datasources.json":
                # Questi file contengono array di oggetti
                vars_array = read_json_file(file_path)
                for var in vars_array:
                    dashboard["templating"]["list"].append(var)
            else:
                # Questi file contengono un singolo oggetto
                var = read_json_file(file_path)
                dashboard["templating"]["list"].append(var)
            print(f"Aggiunte variabili da {filename}")
        except Exception as e:
            print(f"Errore nel caricamento delle variabili da {filename}: {e}")
    
    # Salva la dashboard completa
    dashboard_path = os.path.join(base_dir, "complete_dashboard.json")
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"Dashboard completa salvata in {dashboard_path}")
    
    # Crea directory per la dashboard assemblata
    try:
        subprocess.run(["docker", "exec", "-it", "grafana", "mkdir", "-p", "/etc/grafana/provisioning/dashboards/nearyou"])
        print("Directory creata in Grafana")
    except Exception as e:
        print(f"Errore nella creazione della directory: {e}")
    
    # Copia nel container Grafana
    try:
        subprocess.run(["docker", "cp", dashboard_path, "grafana:/etc/grafana/provisioning/dashboards/nearyou/dashboard.json"])
        print("Dashboard copiata nel container Grafana")
    except Exception as e:
        print(f"Errore nella copia della dashboard nel container: {e}")
    
    # Aggiorna file di configurazione
    config_yaml = """apiVersion: 1

providers:
  - name: 'NearYou'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards/nearyou
"""
    
    config_path = os.path.join(base_dir, "dashboard.yaml")
    with open(config_path, 'w') as f:
        f.write(config_yaml)
    
    try:
        subprocess.run(["docker", "cp", config_path, "grafana:/etc/grafana/provisioning/dashboards/dashboard.yaml"])
        print("File di configurazione copiato nel container Grafana")
    except Exception as e:
        print(f"Errore nella copia del file di configurazione: {e}")
    
    # Riavvia Grafana
    try:
        subprocess.run(["docker", "restart", "grafana"])
        print("Grafana riavviato")
    except Exception as e:
        print(f"Errore nel riavvio di Grafana: {e}")

if __name__ == "__main__":
    create_dashboard()