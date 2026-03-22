# Clase práctica: Ingesta IoT con colas de mensajes

## Contexto

Sigues trabajando para **SensorHub S.L.** En la clase anterior construiste una API REST para recibir lecturas de sensores y generar reportes. El problema: la API está siendo el cuello de botella. Los dispositivos IoT no deberían hablar directamente con la base de datos ni depender de que la API esté disponible.

La solución: introducir un **broker de mensajes** (RabbitMQ) entre los dispositivos y el almacenamiento. Los sensores publican mensajes en una cola; un proceso consumidor los recoge y los inserta en MongoDB en lotes.

**Tu misión: implementar la capa de ingesta por cola y conectarla al sistema existente.**

---



Los dispositivos **no hablan con la API**: publican directamente en la cola. El worker es el único que escribe en MongoDB. La API queda como capa de **consulta y reportes**.

---

## Lo que tienes que implementar

### `app/queue.py`
Wrapper de conexión a RabbitMQ usando la librería `pika`. Necesita:
- Conectarse usando la URL de configuración (`RABBITMQ_URL`)
- Declarar la cola `sensor.readings` como duradera
- Exponer una función `publish(message: dict)` que serialice el mensaje a JSON y lo publique

### `app/worker.py`
El consumidor. Es un proceso independiente (no FastAPI) que:
- Se conecta a RabbitMQ con reintentos (la cola puede no estar lista al arrancar)
- Consume mensajes de `sensor.readings`
- Acumula documentos en un buffer en memoria
- Hace flush del buffer (llama a `insert_many` en MongoDB) cuando:
  - El buffer alcanza `BATCH_SIZE` mensajes, **o**
  - Han pasado `FLUSH_INTERVAL` segundos desde el último flush
- Confirma cada mensaje con `basic_ack` tras añadirlo al buffer
- Se arranca como módulo: `python -m app.worker`

### `simulator.py`
Script local que simula sensores publicando en la cola:
- Define una lista de dispositivos ficticios con `device_id` y `location`
- Genera lecturas aleatorias de temperatura, humedad y CO2
- Las publica en RabbitMQ con la librería `pika`
- Acepta parámetros: `--rate` (mensajes/segundo) y `--total` (nº total, opcional)
- Conecta a `localhost:5672` (se ejecuta fuera de Docker)

### `app/db.py` — nueva función
Añade `insert_many_readings(db, documents: list[dict]) -> int` que use `insert_many()` de pymongo y devuelva el número de documentos insertados.

### `docker-compose.yml` — nuevos servicios
Añade:
- **`rabbitmq`**: imagen `rabbitmq:3-management`. Expone el puerto AMQP (`5672`) y la consola web (`15672`). Necesita healthcheck.
- **`worker`**: usa la misma imagen que la API pero con `command` diferente para arrancar el worker. Depende de `mongo` y `rabbitmq` estando sanos.

### `app/config.py`
Añade `rabbitmq_url: str` a `Settings`.

---

## Endpoints heredados (ya implementados)

Los endpoints de la clase anterior siguen funcionando sin cambios:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado de la API |
| POST | `/readings` | Inserción manual (útil para pruebas) |
| GET | `/readings` | Listar lecturas |
| GET | `/readings/stats` | Estadísticas por dispositivo |
| GET | `/export` | Exportar CSV |
| POST | `/reports/generate` | Generar reporte horario en MinIO |
| GET | `/reports` | Listar reportes |
| GET | `/reports/{report_name}` | Descargar reporte |

---

## Pistas

- `pika` es la librería Python estándar para RabbitMQ (AMQP). `pika.BlockingConnection` con `pika.URLParameters` es el punto de entrada más sencillo.
- La cola debe declararse como `durable=True` y los mensajes como `delivery_mode=2` para que sobrevivan reinicios de RabbitMQ.
- Para el flush por tiempo en el worker, `channel.consume(inactivity_timeout=1)` devuelve `(None, None, None)` cada segundo si no hay mensajes — úsalo para comprobar si toca hacer flush.
- El worker y la API comparten el mismo `Dockerfile`: solo cambia el `command` en docker-compose.
- La consola web de RabbitMQ en `http://localhost:15672` (usuario/contraseña: `guest/guest`) permite ver cuántos mensajes hay en la cola en tiempo real — muy útil para depurar.
- El simulador corre **fuera de Docker**, conectando a `localhost:5672`.

---

**Consulta la documentación oficial y pregunta al profesor cuando lo necesites.**
