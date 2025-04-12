# NearYou 

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
|   └── generate_users.py        # Genero degli utenti attraverso Faker
├── requirements.txt             # Dipendenze Python
└── README.md                    # Questo file
```

## Descrizione Componenti

- **Producer**: genera dati GPS simulati con timestamp in formato ISO-8601 e li invia a Kafka utilizzando Mutual TLS.
- **Consumer**: riceve i dati da Kafka, verifica l’esistenza del database ClickHouse e della tabella necessaria, quindi inserisce i dati nel database.

## Grafana Dashboard
- Attraverso il link presente su ports (3000) apro il browser che linka alla dashboard o https://<workspace-id>-3000.gitpod.io
- Per configurarla si accede con dati di default (admin/admin), nel nostro caso abbiamo cambaito la pw
- Si aggiunge un nuovo **Data Source** , clickhouse non c'è di deafult e quindi sul docker-compose.yml serve l'inclusione di GF_INSTALL_PLUGINS=vertamedia-clickhouse-datasource .
- Per instaurare la connessione :
   - Server Address: clickhouse-server
   - Server Port: 9000
   - Database: nearyou
   - Username e password: quelli inseriti in configrazione su yml.
   - Save & Test
##  ClickHouse:
- E' progettato per analisi ad alte prestazioni su grandi volumi di dati in streaming (OLAP), perfetto per gestire i dati dinamici in tempo reale come quelli provenienti dai simulatori o dai sensori.
- Contiene: users, user_event
## PostgreSQL con PostGIS
- E' ottimizzato per gestire dati statici e relazionali con capacità spaziali avanzate, ideali per memorizzare informazioni sui negozi e eseguire query geospaziali (ad esempio, per verificare la vicinanza degli esercizi commerciali agli utenti).
- All'interno troviamo i punti commerciali

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
## Riavvio completo 
```bash
docker-compose -f .devcontainer/docker-compose.yml restart
```
## Note Aggiuntive

- Il producer genera e invia dati a Kafka, non interagisce direttamente con ClickHouse.
- Il consumer gestisce l’inserimento dati in ClickHouse e crea automaticamente la tabella se non presente.
- Mutual TLS è configurato per sicurezza delle comunicazioni tra Kafka e client.
- Avviare gitpod: https://gitpod.io/#https://github.com/AlphaCodeSWE/NearYou-Project

Per qualsiasi dubbio o ulteriore necessità consultare questo file o contattare il team di sviluppo: alphacodeswe@gmail.com


