import json
from kafka import KafkaConsumer
from clickhouse_driver import Client

#conf
BROKER='kafka:9093'
TOPIC='gps_stream'
COSUMER_GROUP= 'gps_consumer_group'

#inzializzo il consumer di Kakfa

consumer= KafkaConsumer(
    TOPIC,
    bootstrap_server=[BROKER],
    auto_offset_reset='earliest', #leggo dal primo mex disponibile
    group_id=CONSUEMER_GROUP,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

#conn a ClickHouse

clickhouse_client=Client(host='clickhouse-server', user='default', password='pwe@123@l@', port=9000, database='nearyou')

def create_table_if_not_exists():
    tables = client.execute("SHOW TABLES")
    # tables è una lista di tuple, ad esempio [(u'default',), (u'user_events',)...]
    tables_list = [t[0] for t in tables]
    if "user_events" not in tables_list:
        print("La tabella 'user_events' non esiste. Creandola...")
        client.execute('''
            CREATE TABLE IF NOT EXISTS user_events (
                event_id   UInt64,
                event_time DateTime,
                user_id    UInt64,
                latitude   Float64,
                longitude  Float64,
                poi_range  Float64,
                poi_name   String,
                poi_info   String
            ) ENGINE = MergeTree()
            ORDER BY event_id
        ''')
    else:
        print("La tabella 'user_events' esiste già.")

create_table_if_not_exists()

def generate_event_id():
    # Genero un ID evento casuale a 10 cifre così da evitare collisione con eventi
    return random.randint(1000000000, 9999999999)

print("Consumer in ascolto sul topic:", TOPIC)
for message in consumer:
    data = message.value
    # Mappatura dei dati per "user_events"
    event = (
        generate_event_id(),     # event_id
        data['timestamp'],       # event_time
        data['user_id'],         # user_id
        data['latitude'],        # latitude
        data['longitude'],       # longitude
        0.0,                     # poi_range (default: 0.0)
        '',                      # poi_name (default: stringa vuota)
        ''                       # poi_info (default: stringa vuota)
    )
    client.execute(
        'INSERT INTO user_events (event_id, event_time, user_id, latitude, longitude, poi_range, poi_name, poi_info) VALUES',
        [event]
    )
    print("Inserito in DB:", event)
