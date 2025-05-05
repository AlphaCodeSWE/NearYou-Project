import os
import ssl
import json
import asyncio
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

load_dotenv()  

KAFKA_BROKER   = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC    = os.getenv("KAFKA_TOPIC")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")


ssl_context = ssl.create_default_context(cafile=os.getenv("SSL_CAFILE"))
ssl_context.load_cert_chain(
    certfile=os.getenv("SSL_CERTFILE"),
    keyfile=os.getenv("SSL_KEYFILE")
)

# singleton consumer
consumer: AIOKafkaConsumer | None = None

async def connect_consumer():
    global consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        security_protocol="SSL",
        ssl_context=ssl_context,
        value_deserializer=lambda b: json.loads(b.decode("utf-8"))
    )
    await consumer.start()

async def disconnect_consumer():
    global consumer
    if consumer:
        await consumer.stop()
