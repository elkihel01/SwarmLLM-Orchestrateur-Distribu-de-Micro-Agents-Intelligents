
import json
import sys
import uuid

import pika

QUEUE = "llm_tasks"

text = " ".join(sys.argv[1:]) or "J'adore ce nouveau téléphone, la batterie dure deux jours !"

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

# durable=True : la queue survit à un redémarrage de RabbitMQ
channel.queue_declare(queue=QUEUE, durable=True)

message = {"task_id": str(uuid.uuid4()), "text": text}

channel.basic_publish(
    exchange="",                 # exchange par défaut
    routing_key=QUEUE,           # nom de la queue
    body=json.dumps(message),
    properties=pika.BasicProperties(delivery_mode=2),  # message persistant
)

print(f"[producer] Tâche envoyée : {message['task_id']}")
connection.close()
