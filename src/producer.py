import json
import random
import time
from kafka import KafkaProducer

#Conf per kafka
BROKER='kafka:9093'
TOPIC='gps_stream'
MESSAGES_SECOND=5 #numero mex al sec

#inizializzo il KafkaProduer con serializz JSON

producer=KafkaProducer(
    bootstrap_servers=[BROKER],
    value_serializer=lamba v: json.dumps(v).encode('utf-8')
)

def generate_random_gps():
    #uso area di milano per test
    latitudine=random.uniform(45.40, 45.50)
    longitudine=random.uniform(9.10, 9.30)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return{
        "user_id":random.randint(1,1000),
        "latitudine":latitudine
        "longitudine":longitudine
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
        