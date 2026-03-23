"""Simulador de dispositivos IoT.

Publica lecturas de sensores directamente en la cola RabbitMQ,
simulando lo que haría un dispositivo real en producción.

Uso:
    uv run python simulator.py                # 2 msg/s, infinito
    uv run python simulator.py --rate 10      # 10 msg/s
    uv run python simulator.py --total 100    # parar tras 100 mensajes
"""

import argparse
import json
import random
import time
from datetime import UTC, datetime

import pika

RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
QUEUE_NAME = "sensor.readings"

DEVICES = [
    {"device_id": "sensor-01", "location": "Sala Reuniones A"},
    {"device_id": "sensor-02", "location": "Oficina Principal"},
    {"device_id": "sensor-03", "location": "Almacén"},
    {"device_id": "sensor-04", "location": "Sala Reuniones B"},
    {"device_id": "sensor-05", "location": "Recepción"},
]


def simulate(rate: float = 2.0, total: int | None = None) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    total_str = str(total) if total else "infinito"
    print(f"[sim] Conectado. Rate: {rate} msg/s | Total: {total_str} | Ctrl+C para parar\n")

    count = 0
    try:
        while total is None or count < total:
            device = random.choice(DEVICES)
            msg = {
                **device,
                "temperature": round(random.uniform(18.0, 35.0), 1),
                "humidity": round(random.uniform(30.0, 80.0), 1),
                "co2": random.randint(400, 1500),
                "timestamp": datetime.now(UTC).isoformat(),
            }
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=json.dumps(msg),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            count += 1
            print(
                f"[sim #{count:4d}] {msg['device_id']} | {msg['location']:<22} | "
                f"T={msg['temperature']:4.1f}°C  H={msg['humidity']:4.1f}%  CO2={msg['co2']:4d}ppm"
            )
            time.sleep(1 / rate)
    except KeyboardInterrupt:
        print(f"\n[sim] Detenido. Total enviados: {count}")
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de sensores IoT → RabbitMQ")
    parser.add_argument("--rate", type=float, default=2.0, help="Mensajes por segundo (default: 2)")
    parser.add_argument("--total", type=int, default=None, help="Nº total de mensajes (default: infinito)")
    args = parser.parse_args()
    simulate(rate=args.rate, total=args.total)
