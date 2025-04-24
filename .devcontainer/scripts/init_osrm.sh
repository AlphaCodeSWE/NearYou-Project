#!/usr/bin/env bash
set -e

DATA_DIR=/data
PBF_FILE="${DATA_DIR}/milano.osm.pbf"

# 1) Scarica il PBF se non esiste
if [ ! -f "${PBF_FILE}" ]; then
  echo " Scarico PBF di Milano da ${PBF_URL}…"
  curl -sSL "${PBF_URL}" -o "${PBF_FILE}"
  echo " Download completato."
else
  echo " PBF già presente, salto il download."
fi

# 2) Preprocess OSRM
echo " Inizio preprocess OSRM…"
osrm-extract -p /opt/profiles/bicycle.lua "${PBF_FILE}"
osrm-partition "${DATA_DIR}/milano.osrm"
osrm-customize "${DATA_DIR}/milano.osrm"

# 3) Avvia il router
echo " Avvio OSRM routing…"
exec osrm-routed --port 5000 "${DATA_DIR}/milano.osrm"
