#!/usr/bin/env python3
import json
import os
import subprocess

def main():
    # Directory di lavoro
    base_dir = os.getcwd()
    panels_dir = os.path.join(base_dir, "provisioning/dashboards/panels")
    output_file = os.path.join(base_dir, "provisioning/dashboards/nearyou_dashboard.json")
    
    print("=== Creazione dashboard NearYou completa con filtri e mappe ===")
    
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
    
    # Definizione dei pannelli da caricare con le relative posizioni
    panel_configs = [
        {"file": "stat_event.json", "id": 1, "pos": {"h": 4, "w": 12, "x": 0, "y": 0}},
        {"file": "stat_shops.json", "id": 2, "pos": {"h": 4, "w": 12, "x": 12, "y": 0}},
        {"file": "users_table.json", "id": 3, "pos": {"h": 8, "w": 24, "x": 0, "y": 4}},
        {"file": "map_user_routes.json", "id": 4, "pos": {"h": 13, "w": 24, "x": 0, "y": 12}},
        {"file": "map_shops.json", "id": 5, "pos": {"h": 13, "w": 24, "x": 0, "y": 25}}
    ]
    
    # Carica i pannelli dai file JSON
    for config in panel_configs:
        try:
            file_path = os.path.join(panels_dir, config["file"])
            with open(file_path, 'r') as f:
                panel = json.load(f)
            
            # Imposta ID e posizione nel grid
            panel["id"] = config["id"]
            panel["gridPos"] = config["pos"]
            
            # Aggiungi il pannello alla dashboard
            dashboard["panels"].append(panel)
            print(f"Aggiunto pannello da {config['file']} con ID {config['id']}")
        except Exception as e:
            print(f"Errore nel caricamento del pannello {config['file']}: {e}")
    
    # Carica le variabili di template per i filtri
    template_files = [
        "template_age.json",
        "template_profession.json",
        "template_interests.json",
        "template_filters.json",
        "template_datasources.json"
    ]
    
    for template_file in template_files:
        try:
            file_path = os.path.join(panels_dir, template_file)
            with open(file_path, 'r') as f:
                if template_file in ["template_filters.json", "template_datasources.json"]:
                    # Questi file contengono array di oggetti
                    template_data = json.load(f)
                    for item in template_data:
                        dashboard["templating"]["list"].append(item)
                else:
                    # Questi file contengono un singolo oggetto
                    template_data = json.load(f)
                    dashboard["templating"]["list"].append(template_data)
                print(f"Aggiunti filtri da {template_file}")
        except Exception as e:
            print(f"Errore nel caricamento dei filtri da {template_file}: {e}")
    
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
    
    print("\nDashboard completa creata con pannelli, filtri e mappe!")
    print("Accedi a Grafana all'indirizzo http://localhost:3000 con le credenziali admin/admin")

if __name__ == "__main__":
    main()