#!/bin/bash
set -e

GRAFANA_DIR=$(pwd)
BASE_DIR="/workspace/NearYou-Project"

echo "=== Script di riparazione dashboard Grafana ==="
echo "Posizione di lavoro: $GRAFANA_DIR"

# Crea il file di configurazione aggiornato
echo "1. Creazione del file di configurazione"
cat > $GRAFANA_DIR/provisioning/dashboards/dashboard.yaml << 'EOF'
apiVersion: 1

providers:
  - name: 'NearYou'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
EOF

# Crea una dashboard semplice
echo "2. Creazione della dashboard di base"
cat > $GRAFANA_DIR/provisioning/dashboards/near_you_dashboard_assembled.json << 'EOF'
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "grafana-clickhouse-datasource",
        "uid": "ClickHouse"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 4,
        "w": 4,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "title": "Utenti Attivi Oggi",
      "type": "stat"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": ["nearyou", "tracking", "shops"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-24h",
    "to": "now"
  },
  "timepicker": {
    "refresh_intervals": [
      "5s",
      "10s",
      "30s",
      "1m",
      "5m",
      "15m",
      "30m",
      "1h",
      "2h",
      "1d"
    ]
  },
  "timezone": "",
  "title": "NearYou - Analisi Utenti e Negozi",
  "uid": "nearyou-dashboard",
  "version": 1,
  "weekStart": ""
}
EOF

# Copia i file nel container
echo "3. Copiando i file nel container Grafana"
docker cp $GRAFANA_DIR/provisioning/dashboards/dashboard.yaml grafana:/etc/grafana/provisioning/dashboards/
docker cp $GRAFANA_DIR/provisioning/dashboards/near_you_dashboard_assembled.json grafana:/etc/grafana/provisioning/dashboards/

# Riavvia Grafana
echo "4. Riavvio di Grafana"
docker restart grafana

echo "5. Operazione completata!"
echo "Accedi a Grafana all'indirizzo http://localhost:3000 con le credenziali admin/admin"
echo "La dashboard dovrebbe apparire nella home page"