#!/usr/bin/env python3
import json
import os
import subprocess

def main():
    # Directory di lavoro
    base_dir = os.getcwd()
    panels_dir = os.path.join(base_dir, "provisioning/dashboards/panels")
    output_file = os.path.join(base_dir, "provisioning/dashboards/nearyou_dashboard.json")
    
    print(f"=== Creazione dashboard NearYou con statistiche e tabella utenti ===")
    
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
        "title": "NearYou - Dashboard Completa",
        "uid": "nearyou-dashboard",
        "version": 1,
        "weekStart": ""
    }
    
    # Usa i pannelli statistici esistenti per eventi e negozi
    stat_panels = [
        {"file": "stat_event.json", "id": 1, "pos": {"h": 4, "w": 12, "x": 0, "y": 0}},
        {"file": "stat_shops.json", "id": 2, "pos": {"h": 4, "w": 12, "x": 12, "y": 0}}
    ]
    
    # Carica i pannelli statistici
    for panel_def in stat_panels:
        try:
            file_path = os.path.join(panels_dir, panel_def["file"])
            with open(file_path, 'r') as f:
                panel = json.load(f)
            
            # Imposta ID e posizione nel grid
            panel["id"] = panel_def["id"]
            panel["gridPos"] = panel_def["pos"]
            
            # Aggiungi il pannello alla dashboard
            dashboard["panels"].append(panel)
            print(f"Aggiunto pannello {panel_def['file']} con ID {panel_def['id']}")
        except Exception as e:
            print(f"Errore nel caricamento del pannello {panel_def['file']}: {e}")
    
    # Crea un pannello tabella per gli utenti
    users_table = {
        "datasource": {
            "type": "grafana-clickhouse-datasource",
            "uid": "ClickHouse"
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {
                    "align": "auto",
                    "displayMode": "auto",
                    "inspect": False
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}]
                }
            },
            "overrides": []
        },
        "gridPos": {"h": 15, "w": 24, "x": 0, "y": 4},
        "id": 3,
        "options": {
            "footer": {"enablePagination": True},
            "showHeader": True
        },
        "pluginVersion": "10.0.3",
        "targets": [
            {
                "datasource": {
                    "type": "grafana-clickhouse-datasource",
                    "uid": "ClickHouse"
                },
                "format": 1,
                "queryType": "sql",
                "rawSql": "SELECT user_id, username, full_name, email, phone_number, user_type, gender, age, profession, interests, country, city, registration_time FROM nearyou.users",
                "refId": "A"
            }
        ],
        "title": "Lista Utenti Completa",
        "type": "table"
    }
    dashboard["panels"].append(users_table)
    print("Aggiunto pannello tabella utenti")
    
    # Salva la dashboard
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"Dashboard salvata in {output_file}")
    
    # Copia nel container Grafana
    try:
        subprocess.run(["docker", "cp", output_file, "grafana:/etc/grafana/provisioning/dashboards/"])
        print("Dashboard copiata nel container Grafana")
    except Exception as e:
        print(f"Errore nella copia della dashboard nel container: {e}")
    
    # Riavvia Grafana
    try:
        subprocess.run(["docker", "restart", "grafana"])
        print("Grafana riavviato")
    except Exception as e:
        print(f"Errore nel riavvio di Grafana: {e}")
    
    print("\nDashboard creata!")
    print("Accedi a Grafana all'indirizzo http://localhost:3000 con le credenziali admin/admin")

if __name__ == "__main__":
    main()