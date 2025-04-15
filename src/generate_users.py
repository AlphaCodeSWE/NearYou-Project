# src/generate_users.py
#!/usr/bin/env python3
import random
import time
from datetime import datetime
import logging
from clickhouse_driver import Client
from clickhouse_driver.errors import Error as CHError
from faker import Faker
from db_utils import wait_for_clickhouse_database

from logger_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_PORT, CLICKHOUSE_DATABASE

NUM_USERS = 100  # Numero di utenti da generare
fake = Faker('it_IT')

client = Client(
    host=CLICKHOUSE_HOST,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    port=CLICKHOUSE_PORT,
    database=CLICKHOUSE_DATABASE
)

def wait_for_table(table_name: str, timeout: int = 2, max_retries: int = 30) -> bool:
    retries = 0
    while retries < max_retries:
        try:
            tables = client.execute("SHOW TABLES")
            tables_list = [t[0] for t in tables]
            if table_name in tables_list:
                logger.info("La tabella '%s' è disponibile.", table_name)
                return True
            else:
                logger.info("La tabella '%s' non è ancora disponibile. Riprovo...", table_name)
        except CHError as e:
            logger.error("Errore durante il controllo della tabella '%s': %s", table_name, e)
        time.sleep(timeout)
        retries += 1
    raise Exception(f"La tabella '{table_name}' non è stata trovata dopo {max_retries} tentativi.")

def generate_user_record(user_id: int) -> tuple:
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

def insert_users(num_users: int) -> None:
    logger.info("Generazione di %d record utenti...", num_users)
    users = [generate_user_record(i+1) for i in range(num_users)]
    query = '''
        INSERT INTO users (
            user_id, username, full_name, email, phone_number, password, user_type,
            gender, age, profession, interests, country, city, registration_time
        ) VALUES
    '''
    try:
        client.execute(query, users)
        logger.info("Inseriti con successo %d utenti nella tabella 'users'.", num_users)
    except CHError as e:
        logger.error("Errore durante l'inserimento dei record utenti: %s", e)

if __name__ == '__main__':
    # Attendi che il database ClickHouse sia disponibile
    wait_for_clickhouse_database(client, CLICKHOUSE_DATABASE)
    # Attendi che la tabella 'users' sia disponibile
    wait_for_table("users")
    logger.info("Inizio generazione e inserimento dei dati utenti realistici...")
    insert_users(NUM_USERS)
    logger.info("Operazione completata con successo.")
