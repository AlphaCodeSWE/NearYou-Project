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
    group_id=CONSUEMER_GROUP
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

#conn a ClickHouse

clickhouse_client=Client(host='clickhouse-server', user='default', password='pwe@123@l@', port=9000, database='nearyou')

# Creo la tab tabella per i dati GPS se non esiste già
clickhouse_client.execute('''
CREATE TABLE IF NOT EXISTS gps_data (
    user_id UInt64,
    latitude Float64,
    longitude Float64,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY user_id
''')

print("Consumer in ascolto sul topic:", TOPIC)
for message in consumer:
    data = message.value
    # Inserisco il mex in ClickHouse
    clickhouse_client.execute(
        'INSERT INTO gps_data (user_id, latitude, longitude, timestamp) VALUES',
        [(data['user_id'], data['latitude'], data['longitude'], data['timestamp'])]
    )
    print("Inserito in DB:", data)
