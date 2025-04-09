#!/bin/bash
#
# Script per generare keystore e truststore per Kafka con CA self-signed
#
# Esempio d'uso:
#   export STORE_PASS="UnaPasswordSicura_123"
#   ./generate_kafka_ssl.sh
#
# se non impostato: STORE_PASS, lo script ne genera una a caso.

# Se la variabile non esiste, ne generiamo una casuale, se voglio usare in fase di test : STORE_PASS=changeIT
STORE_PASS="${STORE_PASS:-$(openssl rand -base64 16)}"
VALID_DAYS=730  # Durata certificati in giorni 

echo "Utilizzo password keystore/truststore: $STORE_PASS"
echo "(Puoi sovrascriverla impostando STORE_PASS prima di lanciare lo script)."
sleep 2

echo "==== 1) Creazione chiave privata e certificato CA self-signed ===="
openssl genrsa -out ca.key 2048
openssl req -x509 -new -key ca.key -sha256 -days $VALID_DAYS \
  -out ca.crt \
  -subj "/CN=My-Local-CA"

echo "==== 2) Creazione e configurazione del keystore (broker) ===="
keytool -genkey -noprompt \
  -alias kafka-ssl \
  -dname "CN=kafka, OU=Prod, O=MyOrg, L=City, ST=State, C=IT" \
  -keystore kafka.keystore.jks \
  -storepass "$STORE_PASS" \
  -keypass "$STORE_PASS" \
  -keyalg RSA \
  -validity $VALID_DAYS

echo "==== 3) Creazione CSR per il broker (kafka.csr) ===="
keytool -certreq -alias kafka-ssl \
  -keystore kafka.keystore.jks \
  -storepass "$STORE_PASS" \
  -file kafka.csr

echo "==== 4) Firma della CSR con la CA, creando kafka.crt ===="
openssl x509 -req -sha256 -in kafka.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out kafka.crt -days $VALID_DAYS

echo "==== 5) Import CA nel keystore ===="
keytool -import -noprompt \
  -alias my-ca \
  -file ca.crt \
  -keystore kafka.keystore.jks \
  -storepass "$STORE_PASS"

echo "==== 6) Import del certificato firmato (kafka.crt) nel keystore ===="
keytool -import -noprompt \
  -alias kafka-ssl \
  -file kafka.crt \
  -keystore kafka.keystore.jks \
  -storepass "$STORE_PASS"

echo "==== 7) Creazione del truststore (kafka.truststore.jks) ===="
keytool -import -noprompt \
  -alias my-ca \
  -file ca.crt \
  -keystore kafka.truststore.jks \
  -storepass "$STORE_PASS"

echo "=== Fine generazione Keystore & Truststore ==="
echo "File generati:"
echo "  - ca.key  (chiave privata CA)"
echo "  - ca.crt  (certificato CA)"
echo "  - kafka.keystore.jks"
echo "  - kafka.truststore.jks"
echo "  - kafka.csr, kafka.crt"
echo ""
echo "Password keystore/truststore: $STORE_PASS"
