# Teoría de Tests — SensorHub

> Guía para la clase. Agnóstica de lenguaje y framework salvo cuando se mencione explícitamente.

---

## 0. El problema real

Antes de definir nada, el problema concreto:

Tienes `POST /readings`. Quieres saber si funciona. Sin tests, el proceso es:

1. Levantar MongoDB
2. Levantar la API
3. Abrir Postman o curl
4. Mandar el payload a mano
5. Mirar si la respuesta es la correcta
6. Mirar si el documento llegó a la base de datos
7. Repetir para cada caso que te preocupe

Eso cuesta 5 minutos la primera vez. Pero lo harás 50 veces mientras desarrollas, y lo tendrá que hacer cualquiera que toque el código después.

**Un test automatiza exactamente ese proceso.** Nada más, nada menos.

---

## 1. Qué es un test

Un test es código que ejecuta otro código y verifica que el resultado es el esperado.

Estructura mínima — siempre tiene tres fases:

```
ARRANGE  →  preparar el estado inicial (datos, dependencias, configuración)
ACT      →  ejecutar la unidad bajo prueba
ASSERT   →  comprobar que el resultado es el correcto
```

Ejemplo en pseudocódigo con `POST /readings`:

```
# ARRANGE
payload = { device_id: "sensor-01", temperature: 22.5, ... }

# ACT
response = POST /readings con payload

# ASSERT
response.status_code == 201
response.body.message == "Sensor data uploaded successfully"
```

Si el ASSERT falla, el test falla. Si el código cambia y rompe este comportamiento, lo sabemos en milisegundos en vez de en producción.

---

## 2. La pirámide de tests

No todos los tests son iguales. Se clasifican por lo que verifican y lo que cuestan:

```
              /\
             /E2E\              pocos — lentos — costosos — frágiles
            /------\
           /  Inte- \
          / gración  \          algunos — moderados — más realistas
         /------------\
        /              \
       /      Unit       \      muchos — rápidos — baratos — aislados
      /____________________\
```

### Unit tests

Prueban una unidad de lógica en total aislamiento. Todo lo externo (base de datos, red, reloj del sistema) se reemplaza por objetos controlados.

En SensorHub: la función `_parse_document` del worker convierte un mensaje JSON en un documento MongoDB. No necesita ni RabbitMQ ni Mongo para verificar que hace bien la conversión.

```
ARRANGE  →  mensaje = { device_id: "s1", temperature: "22.5", co2: "400" }
ACT      →  resultado = _parse_document(mensaje)
ASSERT   →  resultado.temperature es float 22.5
            resultado.co2 es int 400
            resultado.timestamp existe
```

Esto corre en microsegundos y no necesita infraestructura.

### Integration tests

Prueban que varios componentes funcionan juntos con dependencias reales. El objetivo no es probar la lógica interna sino que la integración entre capas es correcta.

En SensorHub: `POST /readings` → API → MongoDB real. Lo que se verifica es que el documento realmente persiste, con el esquema correcto, y que la query de lectura posterior lo devuelve bien.

Un unit test no puede detectar:
- Que la query de MongoDB está mal escrita
- Que el esquema del documento no coincide con lo que espera la query de lectura
- Bugs de serialización al convertir entre tipos de Python y BSON

Para eso hace falta un test de integración con MongoDB real.

### End-to-end tests (E2E)

Prueban el sistema completo desde el exterior, como lo haría un usuario o un sistema externo. En SensorHub sería: levantar todo el stack (API + MongoDB + MinIO + RabbitMQ), publicar un mensaje en la cola, y verificar que aparece en `GET /readings` después de que el worker lo procese.

Son los más realistas pero también los más lentos, frágiles y caros de mantener. Se usan con criterio, no en cantidad.

### Regla general

Muchos unit tests + algunos integration tests + pocos E2E. Invertir la pirámide (muchos E2E, pocos unit) es el error más común — el resultado es una suite lenta, difícil de depurar y que falla por razones ajenas al código.

---

## 3. Qué es un mock

Un mock es un objeto falso que sustituye a una dependencia real durante el test.

¿Por qué necesitamos mocks?

`POST /readings` llama a `db.upload_sensor_data(...)`. Si en el unit test usamos MongoDB real:
- El test tarda cientos de milisegundos en vez de microsegundos
- El test falla si MongoDB no está levantado
- El test deja estado en la base de datos que puede contaminar otros tests
- No podemos controlar qué devuelve MongoDB para simular casos de error

Con un mock, `db` es un objeto que podemos configurar:

```
mock_db.upload_sensor_data()  →  no hace nada (por defecto)
mock_db.read_sensor_data()    →  devuelve exactamente lo que queramos
mock_db.read_sensor_data()    →  lanza una excepción si queremos probar ese caso
```

Además, el mock registra cómo fue llamado, lo que nos permite hacer aserciones sobre el comportamiento:

```
ASSERT  →  mock_db.upload_sensor_data fue llamado exactamente 1 vez
ASSERT  →  fue llamado con los argumentos correctos
```

Esto es importante: **en un unit test no verificamos que los datos llegan a MongoDB, verificamos que el código llama a la capa correcta con los argumentos correctos.** Que MongoDB haga bien su trabajo es responsabilidad del integration test.

### La trampa del mock excesivo

Mockear todo es tentador porque hace los tests rápidos y sin dependencias. Pero si mockeas tanto que el test ya no prueba nada real, pierdes el valor.

Señal de alerta: si cambias la implementación interna sin cambiar el comportamiento observable, y el test falla — el test está probando la implementación, no el comportamiento. Eso es un mock mal colocado.

Regla práctica: mockea en el límite del sistema (base de datos, red, reloj, sistema de ficheros). No mockees lógica de negocio propia.

---

## 4. Fixtures

Una fixture es código de preparación reutilizable que se ejecuta antes de un test (y opcionalmente hace limpieza después).

En vez de repetir la creación del cliente HTTP y el mock de la base de datos en cada test:

```
# Sin fixture — repetición en cada test
test_health:
    client = crear cliente HTTP
    mock_db = crear mock
    ...

test_post_reading:
    client = crear cliente HTTP
    mock_db = crear mock
    ...
```

Una fixture lo centraliza:

```
fixture client(mock_db):
    return crear cliente HTTP con mock_db inyectado

fixture mock_db:
    return mock de MongoDB
```

Cualquier test que declare `client` como parámetro recibe automáticamente un cliente listo, con su mock, sin repetir código.

### Scope de las fixtures

El scope controla cuántas veces se ejecuta la fixture:

- **function** (por defecto): se ejecuta antes y después de cada test. El estado es completamente fresco para cada uno. Costoso si la fixture levanta infraestructura.
- **session**: se ejecuta una sola vez para toda la suite. Apropiado para operaciones costosas como levantar contenedores Docker.

En SensorHub, `docker_services` tenía scope de sesión porque levantar MongoDB y MinIO para cada test haría la suite inutilizablemente lenta.

Consecuencia importante: con scope de sesión, el estado **se acumula entre tests**. Si el test A inserta datos y el test B lee `GET /readings`, el test B verá los datos del test A. Solución: fixture de limpieza con `autouse=True` que borra los datos antes de cada test, aunque los contenedores sigan levantados.

---

## 5. Qué hace que un test sea bueno

### Determinista

El mismo test, en cualquier máquina, en cualquier momento, debe dar siempre el mismo resultado. Un test que a veces pasa y a veces falla (flaky test) es peor que no tener test — genera ruido, erode la confianza en la suite, y se termina ignorando.

Causas comunes de tests no deterministas:
- Dependencia del tiempo real (`datetime.now()`)
- Dependencia del orden de ejecución
- Estado compartido entre tests no limpiado
- Red o servicios externos sin controlar

### Aislado

Cada test debe poder ejecutarse solo o en cualquier orden sin que el resultado cambie. Si el test B solo pasa porque el test A lo ejecutó antes, tienes un problema de estado compartido.

### Nombrado para describir el fallo

El nombre del test debe responder: **¿qué comportamiento se rompe cuando este test falla?**

```
# Malo
test_1()
test_readings()
test_post()

# Bueno
test_post_reading_returns_201()
test_post_reading_calls_database()
test_get_readings_filtered_by_device_id()
test_stats_empty_when_no_data()
```

Cuando falla `test_post_reading_calls_database` a las 3am sabes exactamente dónde mirar. Cuando falla `test_2` no sabes nada.

### Prueba comportamiento, no implementación

Un test que prueba comportamiento verifica **qué hace** el sistema desde fuera.
Un test que prueba implementación verifica **cómo lo hace** por dentro.

```
# Prueba implementación — frágil
ASSERT  →  se llamó a df.groupby("device_id")

# Prueba comportamiento — robusto
ASSERT  →  GET /readings/stats devuelve avg_temperature = 23.0 para sensor-01
```

El primero falla si refactorizas el cálculo (aunque el resultado sea idéntico). El segundo solo falla si el comportamiento observable cambia. Tests frágiles son tests que se rompen sin que nada haya empeorado, y generan el mismo ruido que los tests que detectan bugs reales.

### Rápido

Los unit tests deben correr en milisegundos. La suite completa de unit tests debe terminar en segundos. Si tardan mucho, los desarrolladores dejan de ejecutarlos localmente y pierden su valor como herramienta de feedback rápido.

Para SensorHub, 23 tests en 0.06 segundos. Si ese número crece a 30 segundos, algo está mal (probablemente hay tests unitarios que acceden a servicios reales).

---

## 6. Qué NO es un test de calidad

- **Un test que siempre pasa.** Si un test nunca puede fallar, no está probando nada. A veces un mock mal configurado hace que el test pase sin importar lo que devuelva el código real.

- **Un test que repite el código de producción.** Si el test calcula lo mismo que calcula el código para generar el expected, el test no tiene valor. El expected debe ser un valor concreto conocido de antemano.

  ```
  # Malo — repite la lógica
  expected = (22.0 + 24.0) / 2   # mismo cálculo que hace el código
  assert result == expected

  # Bueno — valor conocido
  assert result == 23.0
  ```

- **Un test que prueba el framework o la librería.** No hay que probar que FastAPI serializa JSON correctamente — eso ya lo prueba FastAPI. Prueba tu lógica.

- **Un test con lógica condicional.** Si un test tiene `if` o bucles no triviales, probablemente necesita dividirse en varios tests más simples, cada uno con un único flujo.

---

## 7. Cobertura de código

La cobertura (coverage) mide qué porcentaje de líneas del código de producción son ejecutadas por los tests.

Es una métrica útil para detectar código nunca probado. Pero:

- **100% de cobertura no significa 0 bugs.** Puedes ejecutar una línea sin verificar que hace lo correcto.
- **Una cobertura baja es una señal de alerta.** Código no cubierto es código del que no sabes si funciona.
- **No optimices para el número.** Un test que solo existe para subir el porcentaje, sin ninguna aserción útil, es peor que no tener test.

Úsala como herramienta de diagnóstico: ¿hay rutas de error que nunca se prueban? ¿Hay módulos enteros sin cobertura? Eso es lo que importa.

---

## 8. El ciclo de desarrollo con tests

El flujo saludable no es "escribir código, luego escribir tests". Es:

```
1. Entiendes qué tiene que hacer el código
2. Escribes el test que describe ese comportamiento
3. El test falla (el código no existe o no hace lo correcto)
4. Escribes el código mínimo para que el test pase
5. Refactorizas si hace falta — los tests garantizan que no rompes nada
6. Vuelves al paso 1
```

Esto es TDD (Test-Driven Development). No es obligatorio seguirlo al pie de la letra, pero tiene una ventaja concreta: te fuerza a pensar en la interfaz y el comportamiento antes que en la implementación.

Cuando primero escribes el código y luego los tests, tiendes a escribir tests que encajan con la implementación que ya tienes, no tests que describen el comportamiento que quieres. El resultado suele ser tests más frágiles.

---

## 9. Tests y CI (Continuous Integration)

El valor de los tests se multiplica cuando se ejecutan automáticamente en cada cambio de código.

CI (Integración Continua) es el sistema que, en cada push o pull request:
1. Descarga el código
2. Instala dependencias
3. Ejecuta los tests
4. Bloquea el merge si alguno falla

Esto garantiza que nadie integra código roto en la rama principal, sin depender de que alguien recuerde ejecutar los tests manualmente.

```
developer push
      │
      ▼
  CI ejecuta tests
      │
   ┌──┴──┐
   │     │
  PASS  FAIL
   │     │
merge   ✗  bloqueo — no se puede mergear
```

Para SensorHub, el flujo natural sería:
- **Unit tests**: en cada push, siempre. Son rápidos y no necesitan infraestructura.
- **Integration tests**: en pull requests o en la rama principal. Necesitan Docker, tardan más.

La separación entre unit e integration en carpetas distintas no es estética — es para poder ejecutarlos selectivamente según el contexto.

---

## 10. Resumen: el contrato de cada capa

| | Unit | Integration | E2E |
|---|---|---|---|
| **Qué prueba** | Lógica aislada | Integración entre capas | Sistema completo |
| **Dependencias** | Todo mockeado | Servicios reales (BD, etc.) | Stack completo |
| **Velocidad** | Milisegundos | Segundos | Minutos |
| **Cuántos** | Muchos | Algunos | Pocos |
| **Qué detecta** | Bugs de lógica | Bugs de integración | Regresiones de flujo completo |
| **Qué NO detecta** | Bugs de integración | Bugs de lógica de UI | Bugs de lógica interna |

Ninguna capa sustituye a otra. Se complementan.

---

## Conceptos clave

| Término | Definición breve |
|---|---|
| **Test** | Código que verifica el comportamiento de otro código |
| **AAA** | Arrange / Act / Assert — las tres fases de un test |
| **Mock** | Sustituto controlado de una dependencia externa |
| **Fixture** | Código de preparación reutilizable entre tests |
| **Scope** | Cuántas veces se ejecuta una fixture (por test o por sesión) |
| **Coverage** | Porcentaje de líneas de producción ejecutadas por tests |
| **Flaky test** | Test que da resultados distintos sin cambios en el código |
| **TDD** | Escribir el test antes que el código de producción |
| **CI** | Sistema que ejecuta los tests automáticamente en cada cambio |
| **Test de comportamiento** | Verifica qué hace el sistema desde fuera |
| **Test de implementación** | Verifica cómo lo hace por dentro — frágil |
