import json
import random
import time
from kafka import KafkaProducer

# Conf per kafka
BROKER = 'kafka:9093'   # Porta SSL
TOPIC = 'gps_stream'
MESSAGES_PER_SECOND = 5

# Configura i percorsi dei certificati (adatta i path se necessario)
SSL_CAFILE = '/workspace/certs/ca.pem'
SSL_CERTFILE = '/workspace/certs/client_cert.pem'
SSL_KEYFILE = '/workspace/certs/client_key.pem'

# Inizializza il KafkaProducer con SSL
producer = KafkaProducer(
    bootstrap_servers=[BROKER],
    security_protocol='SSL',
    ssl_check_hostname=True,      # In produzione è preferibile lasciarlo True se i certificati sono validi
    ssl_cafile=SSL_CAFILE,
    ssl_certfile=SSL_CERTFILE,
    ssl_keyfile=SSL_KEYFILE,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_random_gps():
    #uso area di milano per test
    lat=random.uniform(45.40, 45.50)
    lon=random.uniform(9.10, 9.30)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return{
        "user_id":random.randint(1,1000),
        "latitudine":lat,
        "longitudine":lon,
        "timestamp":timestamp
    }

if __name__ == '__main__':
    print("Avvio simulatore dati GPS")
    while True:
        message=generate_random_gps
        producer.send(TOPIC,message)
        producer.flush() #mi assicuro che il mex venga inviato all'sistante
        printf(f"inviato:{message}")
        time.sleep(1.0/ MESSAGES_SECOND)
        