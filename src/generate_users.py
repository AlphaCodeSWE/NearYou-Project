#!/usr/bin/env python3
import random
import time
from datetime import datetime
import logging
from clickhouse_driver import Client
from clickhouse_driver.errors import Error as CHError
from faker import Faker

# Configurazioni per ClickHouse
CLICKHOUSE_HOST = 'clickhouse-server'
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = 'pwe@123@l@'
CLICKHOUSE_PORT = 9000
DATABASE = 'nearyou'

# Numero di utenti da generare
NUM_USERS = 100

# Configura il logger per registrare le operazioni
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inizializza Faker in ita
fake = Faker('it_IT')

# Crea il client ClickHouse
client = Client(
    host=CLICKHOUSE_HOST,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    port=CLICKHOUSE_PORT,
    database=DATABASE
)

def wait_for_database(db_name, timeout=2, max_retries=30):
    """Attende finché il database specificato esiste in ClickHouse."""
    retries = 0
    while retries < max_retries:
        try:
            databases = client.execute("SHOW DATABASES")
            databases_list = [db[0] for db in databases]
            if db_name in databases_list:
                logging.info("Database '%s' disponibile.", db_name)
                return True
            else:
                logging.info("Database '%s' non ancora disponibile. Riprovo...", db_name)
        except CHError as e:
            logging.error("Errore durante la verifica del database: %s", e)
        time.sleep(timeout)
        retries += 1
    raise Exception(f"Il database '{db_name}' non è stato trovato dopo {max_retries} tentativi.")

def wait_for_table(table_name, timeout=2, max_retries=30):
    """Attende finché la tabella specificata esiste nel database."""
    retries = 0
    while retries < max_retries:
        try:
            tables = client.execute("SHOW TABLES")
            tables_list = [t[0] for t in tables]
            if table_name in tables_list:
                logging.info("La tabella '%s' è disponibile.", table_name)
                return True
            else:
                logging.info("La tabella '%s' non è ancora disponibile. Riprovo...", table_name)
        except CHError as e:
            logging.error("Errore durante il controllo della tabella '%s': %s", table_name, e)
        time.sleep(timeout)
        retries += 1
    raise Exception(f"La tabella '{table_name}' non è stata trovata dopo {max_retries} tentativi.")

def generate_user_record(user_id):
    
    gender = random.choice(["Male", "Female"])
    user_type = random.choice(["free", "premium"])
    return (
        user_id,
        fake.user_name(),
        fake.name(),
        fake.email(),
        fake.phone_number(),
        fake.password(length=10),
        user_type,
        gender,
        random.randint(18, 80),
        fake.job(),
        ", ".join(fake.words(nb=3)),
        fake.country(),
        fake.city(),
        datetime.now()  # Timestamp di registrazione
    )

def insert_users(num_users):
    """
    Genera e inserisce 'num_users' record nella tabella 'users'.
    """
    logging.info("Generazione di %d record utenti...", num_users)
    users = [generate_user_record(user_id=i+1) for i in range(num_users)]
    query = '''
        INSERT INTO users (
            user_id, username, full_name, email, phone_number, password, user_type,
            gender, age, profession, interests, country, city, registration_time
        ) VALUES
    '''
    try:
        client.execute(query, users)
        logging.info("Inseriti con successo %d utenti nella tabella 'users'.", num_users)
    except CHError as e:
        logging.error("Errore durante l'inserimento dei record utenti: %s", e)

if __name__ == '__main__':
    logging.info("Verifica disponibilità del database '%s'...", DATABASE)
    wait_for_database(DATABASE)
    logging.info("Attesa disponibilità della tabella 'users'...")
    wait_for_table("users")
    logging.info("Inizio generazione e inserimento dei dati utenti realistici...")
    insert_users(NUM_USERS)
    logging.info("Operazione completata con successo.")
