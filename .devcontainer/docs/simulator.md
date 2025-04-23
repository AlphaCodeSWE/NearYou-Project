# Documentazione del Simulatore di Dati GPS

Questo documento descrive il **simulatore di dati GPS e profilo utente** implementato in `src/producer.py`. L'obiettivo del simulatore è generare in streaming eventi che combinano informazioni di posizione (GPS) e profiling utente, e pubblicarli su un broker Kafka.

## Componenti Principali

1. **`generate_random_profile()`**
   - Genera un mini-profilo utente casuale:
     - Età (`age`)
     - Professione (`profession`)
     - Interessi (`interests`)

2. **`generate_random_gps_message()`**
   - Calcola latitudine e longitudine casuali in un range predefinito (area di Milano).
   - Assegna un `user_id` casuale.
   - Seleziona uno shop casuale (nome e categoria).
   - Combina i dati di GPS, profilo e shop in un payload JSON.

3. **`json_serializer()`**
   - Helper per serializzare oggetti `datetime` in stringhe ISO-8601 prima dell'invio.

4. **Loop principale**
   - Attende la disponibilità del broker Kafka.
   - Istanzia un `KafkaProducer` con SSL mutual-TLS.
   - In un ciclo infinito:
     - Genera un messaggio con `generate_random_gps_message()`.
     - Esegue `producer.send()` verso il topic configurato.
     - Gestisce il flush ogni `BATCH_SIZE` messaggi.
     - Paga una pausa (`sleep`) per regolare la velocità di invio.

## Flowchart del Flusso di Esecuzione

```mermaid
flowchart LR
    Start[Start Producer Script]
    Start --> WaitBroker{Wait for Kafka Broker}
    WaitBroker -->|available| InitProducer[Initialize KafkaProducer]
    InitProducer --> GenerateMsg[Generate Random GPS Message]
    GenerateMsg --> Serialize[Serialize to JSON]
    Serialize --> SendKafka[Send to Kafka Topic]
    SendKafka --> Increment[Increment batch counter]
    Increment --> CheckBatch{Batch counter ≥ BATCH_SIZE?}
    CheckBatch -- Yes --> Flush[producer.flush()]
    CheckBatch -- No --> Sleep[time.sleep(0.8s)]
    Flush --> ResetCounter[Reset batch counter]
    ResetCounter --> Sleep
    Sleep --> GenerateMsg
```

## Schema Logico-Concettuale

```plaintext
+--------------------------------------+        +-------------------------+
|    Simulatore (producer.py)          |        |   Broker Kafka          |
|                                      |  send  |  Topic: gps_stream      |
|  - Genera profilo utente             |------->|                         |
|  - Genera coordinate GPS             |        +-------------------------+
|  - Seleziona shop casuale            |                   ^
|  - Combina in payload JSON           |                   |
|  - Invia batch di messaggi           |-------------------+
+--------------------------------------+
```

## Parametri di Configurazione

- **KAFKA_BROKER**: host:port del broker (default `kafka:9093`)
- **KAFKA_TOPIC**: topic Kafka (default `gps_stream`)
- **SSL_CAFILE, SSL_CERTFILE, SSL_KEYFILE**: percorsi certificati SSL mutual
- **BATCH_SIZE**: numero di messaggi prima di `flush()` (default 5)
- **Sleep Interval**: pausa tra invii per controllare il rate (default 0.8s)

## Istruzioni di Utilizzo

1. Avvia il container Kafka e assicurati che il broker sia in ascolto.
2. Esegui il simulatore:
   ```bash
   python3 src/producer.py
   ```
3. I messaggi saranno visibili nel topic configurato e potranno essere consumati da altri componenti per l'elaborazione.


