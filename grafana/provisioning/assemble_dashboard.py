#!/usr/bin/env python3
import json
import os
import subprocess

def main():
    # Directory di lavoro
    base_dir = os.getcwd()
    panels_dir = os.path.join(base_dir, "provisioning/dashboards/panels")
    output_file = os.path.join(base_dir, "provisioning/dashboards/nearyou_dashboard.json")
    
    print(f"=== Creazione dashboard NearYou con pannelli statistici ===")
    
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
        "title": "NearYou - Statistiche Base",
        "uid": "nearyou-stats",
        "version": 1,
        "weekStart": ""
    }
    
    # Definizione solo dei pannelli statistici
    panel_definitions = [
        {"file": "stat_users.json", "id": 1, "pos": {"h": 4, "w": 8, "x": 0, "y": 0}},
        {"file": "stat_event.json", "id": 2, "pos": {"h": 4, "w": 8, "x": 8, "y": 0}},
        {"file": "stat_shops.json", "id": 3, "pos": {"h": 4, "w": 8, "x": 16, "y": 0}}
    ]
    
    # Carica ciascun pannello definito
    for panel_def in panel_definitions:
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
    
    print("\nDashboard con statistiche di base creata!")
    print("Accedi a Grafana all'indirizzo http://localhost:3000 con le credenziali admin/admin")

if __name__ == "__main__":
    main()