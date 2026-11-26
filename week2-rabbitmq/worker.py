import json

import httpx
import pika

QUEUE = "llm_tasks"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"

SYSTEM_PROMPT = (
    "Tu es un assistant d'analyse de texte. "
    "Tu réponds uniquement en JSON, en français, avec les champs : "
    "resume (une phrase), sentiment (positif, négatif ou neutre), "
    "mots_cles (liste de 3 à 5 mots)."
)


def call_ollama(text: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "format": "json",
        "stream": False,
    }
    r = httpx.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


def on_message(ch, method, properties, body):
    task = json.loads(body)
    print(f"[worker] Tâche reçue : {task['task_id']}")
    try:
        result = call_ollama(task["text"])
        print("[worker] Résultat :")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        ch.basic_ack(delivery_tag=method.delivery_tag)       # tâche terminée
    except Exception as e:
        print(f"[worker] Erreur : {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  # rejette sans boucle infinie


connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.queue_declare(queue=QUEUE, durable=True)

# Un seul message à la fois par worker (le LLM est lent)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=QUEUE, on_message_callback=on_message)

print("[worker] En attente de messages. CTRL+C pour arrêter.")
channel.start_consuming()