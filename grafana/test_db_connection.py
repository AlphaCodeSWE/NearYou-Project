#!/usr/bin/env python3
import json
import os
import subprocess

def main():
    grafana_dir = os.getcwd()
    output_file = os.path.join(grafana_dir, "provisioning/dashboards/test_db_connection.json")
    
    print(f"=== Test della connessione ai database ===")
    
    # Crea una dashboard di test con due pannelli (uno per ClickHouse e uno per PostgreSQL)
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
        "panels": [
            # Pannello ClickHouse
            {
                "datasource": {
                    "type": "grafana-clickhouse-datasource",
                    "uid": "ClickHouse"
                },
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}]
                        }
                    },
                    "overrides": []
                },
                "gridPos": {"h": 4, "w": 12, "x": 0, "y": 0},
                "id": 1,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                },
                "title": "Test ClickHouse - Conteggio Utenti",
                "type": "stat",
                "targets": [
                    {
                        "datasource": {
                            "type": "grafana-clickhouse-datasource",
                            "uid": "ClickHouse"
                        },
                        "format": 1,
                        "queryType": "sql",
                        "rawSql": "SELECT COUNT(*) FROM nearyou.users",
                        "refId": "A"
                    }
                ]
            },
            # Pannello PostgreSQL
            {
                "datasource": {
                    "type": "postgres",
                    "uid": "PostgreSQL"
                },
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}]
                        }
                    },
                    "overrides": []
                },
                "gridPos": {"h": 4, "w": 12, "x": 12, "y": 0},
                "id": 2,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                },
                "title": "Test PostgreSQL - Conteggio Shops",
                "type": "stat",
                "targets": [
                    {
                        "datasource": {
                            "type": "postgres",
                            "uid": "PostgreSQL"
                        },
                        "format": "table",
                        "rawQuery": True,
                        "rawSql": "SELECT COUNT(*) FROM shops",
                        "refId": "A"
                    }
                ]
            }
        ],
        "refresh": "5s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["test", "nearyou"],
        "templating": {"list": []},
        "time": {"from": "now-24h", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
        },
        "timezone": "",
        "title": "NearYou - Test Connessioni Database",
        "uid": "nearyou-test-db",
        "version": 1,
        "weekStart": ""
    }
    
    # Salva la dashboard di test
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"Dashboard di test salvata in {output_file}")
    
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
    
    print("\nTest completato!")
    print("Accedi a Grafana all'indirizzo http://localhost:3000 con le credenziali admin/admin")
    print("Verifica nella dashboard di test se i pannelli mostrano correttamente i dati dai database")

if __name__ == "__main__":
    main()