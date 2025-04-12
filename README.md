# NearYou - Smart Custom Advertising Platform

Questa repository contiene il codice e la configurazione necessari per eseguire una piattaforma di advertising personalizzata basata su flussi dati GPS inviati a Kafka e archiviati in ClickHouse. Il progetto utilizza comunicazione sicura tramite Mutual TLS.

## Struttura della Repository

```
NearYou-Project/
├── .devcontainer/
│   ├── docker-compose.yml       # Configurazione Docker Compose
│   ├── Dockerfile               # Dockerfile per il devcontainer
│   ├── devcontainer.json        # Configurazione per VSCode
│   └── scripts/
│       └── init_clickhouse.sh   # Script inizializzazione ClickHouse
├── certs/
│   ├── ca.crt                   # Certificato CA
│   ├── ca.key                   # Chiave privata CA
│   ├── ca.srl                   # File seriale CA
│   ├── kafka.keystore.jks       # Keystore Kafka
│   ├── kafka.truststore.jks     # Truststore Kafka
│   ├── client_key.pem           # Chiave privata client
│   ├── client_cert.pem          # Certificato client
│   └── client.csr               # CSR per il client
├── src/
│   ├── producer.py              # Producer Kafka
│   └── consumer.py              # Consumer Kafka e ClickHouse
├── requirements.txt             # Dipendenze Python
└── README.md                    # Questo file
```

## Descrizione Componenti

- **Producer**: genera dati GPS simulati con timestamp in formato ISO-8601 e li invia a Kafka utilizzando Mutual TLS.
- **Consumer**: riceve i dati da Kafka, verifica l’esistenza del database ClickHouse e della tabella necessaria, quindi inserisce i dati nel database.

## Configurazione Iniziale

### Avviare Ambiente Docker Compose

```bash
docker-compose -f .devcontainer/docker-compose.yml down
docker-compose -f .devcontainer/docker-compose.yml up --build -d
```

### Verifica dello stato dei Container

```bash
docker-compose -f .devcontainer/docker-compose.yml ps
```

### Controllo Log dei Container

- **Producer**:

```bash
docker-compose -f .devcontainer/docker-compose.yml logs producer
```

- **Consumer**:

```bash
docker-compose -f .devcontainer/docker-compose.yml logs consumer
```

## Verifica Database ClickHouse

Accedere al container ClickHouse:

```bash
docker exec -it clickhouse-server clickhouse-client
```

Eseguire i seguenti comandi SQL:

```sql
USE nearyou;
SHOW TABLES;
SELECT * FROM user_events LIMIT 10;
```

## Generazione Certificati Client Mutual TLS

Entrare nella directory certificati:

```bash
cd certs
```

Generare CSR e chiave privata del client:

```bash
openssl req -new -nodes -out client.csr -newkey rsa:2048 -keyout client_key.pem -subj "/C=IT/ST=Italia/L=Roma/O=ExampleOrg/CN=client-$(openssl rand -hex 4)"
```

Firmare il certificato client con la CA:

```bash
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client_cert.pem -days 365 -sha256
```

Verificare i file generati:

```bash
ls -la
```

Dovresti visualizzare i file:
- `client_key.pem`
- `client_cert.pem`
- `client.csr`

## Controllo Certificati nei Container

Per verificare la presenza dei certificati nei container:

```bash
docker-compose -f .devcontainer/docker-compose.yml exec consumer ls -la /workspace/certs
```

## Note Aggiuntive

- Il producer genera e invia dati a Kafka, non interagisce direttamente con ClickHouse.
- Il consumer gestisce l’inserimento dati in ClickHouse e crea automaticamente la tabella se non presente.
- Mutual TLS è configurato per sicurezza delle comunicazioni tra Kafka e client.
- Avviare gitpod: https://gitpod.io/#https://github.com/AlphaCodeSWE/NearYou-Project

Per qualsiasi dubbio o ulteriore necessità consultare questo file o contattare il team di sviluppo: alphacodeswe@gmail.com


