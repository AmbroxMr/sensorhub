"""Worker: consume mensajes de RabbitMQ e inserta en MongoDB por lotes.

Arrancar:
    uv run python -m sensorhub.worker
"""

import json
import time
from datetime import UTC, datetime

import pika
import pika.exceptions

from sensorhub.config import Settings
from sensorhub.mongo import MongoDB

settings = Settings()  # type: ignore[call-arg]
QUEUE_NAME = "sensor.readings"
BATCH_SIZE = 50
FLUSH_INTERVAL = 5


def _parse_document(msg: dict) -> dict:
    ts_raw = msg.get("timestamp")
    return {
        "device_id": msg["device_id"],
        "location": msg["location"],
        "temperature": float(msg["temperature"]),
        "humidity": float(msg["humidity"]),
        "co2": int(msg["co2"]),
        "timestamp": datetime.fromisoformat(ts_raw) if ts_raw else datetime.now(UTC),
        "source": "queue",
    }


def run() -> None:
    db = MongoDB()
    buffer: list[dict] = []
    last_flush = time.time()

    connection = None
    while connection is None:
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(settings.rabbitmq_url)
            )
        except pika.exceptions.AMQPConnectionError:
            print("[worker] RabbitMQ no disponible, reintentando en 3s...")
            time.sleep(3)

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=BATCH_SIZE)
    print(
        f"[worker] Escuchando en '{QUEUE_NAME}' — batch={BATCH_SIZE}, flush cada {FLUSH_INTERVAL}s"
    )

    def flush() -> None:
        nonlocal buffer, last_flush
        if buffer:
            count = db.insert_many(buffer)
            print(f"[worker] Flush: {count} documentos insertados en MongoDB")
            buffer = []
        last_flush = time.time()

    for method, _props, body in channel.consume(queue=QUEUE_NAME, inactivity_timeout=1):
        if method is None:
            if buffer and time.time() - last_flush >= FLUSH_INTERVAL:
                flush()
            continue

        doc = _parse_document(json.loads(body))
        buffer.append(doc)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print(
            f"[worker] Recibido: {doc['device_id']} | CO2={doc['co2']}ppm (buffer={len(buffer)})"
        )

        if len(buffer) >= BATCH_SIZE:
            flush()

    connection.close()


if __name__ == "__main__":
    run()
