import json
import logging
import pika
from app.config import RABBITMQ_URL

logger = logging.getLogger("Middleware-Events")
EXCHANGE = "mercado.eventos"


def _conectar():
    params = pika.URLParameters(RABBITMQ_URL)
    params.socket_timeout = 1
    params.blocked_connection_timeout = 1
    return pika.BlockingConnection(params)


def ping() -> bool:
    try:
        conn = _conectar()
        conn.close()
        return True
    except Exception:
        return False


def publicar(routing_key: str, payload: dict) -> bool:
    try:
        conn = _conectar()
        canal = conn.channel()
        canal.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        canal.queue_declare(queue=routing_key, durable=True)
        canal.queue_bind(queue=routing_key, exchange=EXCHANGE, routing_key=routing_key)
        canal.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
        )
        conn.close()
        logger.info("[RABBITMQ] Evento %s publicado.", routing_key)
        return True
    except Exception as exc:
        logger.warning("[RABBITMQ] No disponible al publicar %s: %s", routing_key, exc)
        return False
