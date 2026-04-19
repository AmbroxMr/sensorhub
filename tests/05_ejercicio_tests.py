"""
Ejercicio: escribe los tests de clasificar_lectura()
=====================================================

La función recibe los valores de un sensor y devuelve el nivel de la sala:

    "normal"  →  todos los valores dentro del rango óptimo
    "aviso"   →  algún valor fuera del rango óptimo pero dentro del aceptable
    "alerta"  →  algún valor fuera del rango aceptable

Rangos:
                  óptimo          aceptable
    CO2           < 800 ppm       < 1200 ppm
    Temperatura   20–24 °C        18–26 °C
    Humedad       40–60 %         30–70 %

Lanza ValueError si algún valor es físicamente imposible
(co2 < 0, temperatura < -50 o > 100, humedad < 0 o > 100).

Comandos:
    pytest 05_ejercicio_tests.py -v          # ejecutar los tests
    pytest 05_ejercicio_tests.py -v --tb=short   # con traceback corto
"""

import pytest  # noqa: F401  — los alumnos lo necesitan para pytest.raises


# ---------------------------------------------------------------------------
# Código de producción
# ---------------------------------------------------------------------------


def clasificar_lectura(co2: float, temperatura: float, humedad: float) -> str:
    if (
        co2 < 0
        or temperatura < -50
        or temperatura > 100
        or humedad < 0
        or humedad > 100
    ):
        raise ValueError("Valores fuera de rango físico")

    co2_optimo = co2 < 800
    temp_optima = 20 <= temperatura <= 24
    hum_optima = 40 <= humedad <= 60

    co2_ok = co2 < 1200
    temp_ok = 18 <= temperatura <= 26
    hum_ok = 30 <= humedad <= 70

    if co2_optimo and temp_optima and hum_optima:
        return "normal"
    if co2_ok and temp_ok and hum_ok:
        return "aviso"
    return "alerta"


# ---------------------------------------------------------------------------
# Tests — completa los que faltan
# ---------------------------------------------------------------------------


def test_normal_cuando_todo_esta_en_rango_optimo():
    assert clasificar_lectura(co2=500, temperatura=22.0, humedad=50.0) == "normal"


def test_aviso_cuando_co2_supera_rango_optimo():
    # co2=900 está fuera del óptimo (< 800) pero dentro del aceptable (< 1200)
    assert clasificar_lectura(co2=900, temperatura=22.0, humedad=50.0) == "aviso"


def test_alerta_cuando_co2_supera_rango_aceptable():
    raise NotImplementedError("Escribe este test")


def test_aviso_cuando_temperatura_supera_rango_optimo():
    raise NotImplementedError("Escribe este test")


def test_alerta_cuando_temperatura_supera_rango_aceptable():
    raise NotImplementedError("Escribe este test")


def test_aviso_cuando_humedad_fuera_de_rango_optimo():
    raise NotImplementedError("Escribe este test")


def test_limite_co2_optimo_exacto():
    # 799 es normal, 800 ya no lo es — prueba los dos
    raise NotImplementedError("Escribe este test")


def test_limite_temperatura_aceptable_exacto():
    # 18.0 es aviso, 17.9 es alerta
    raise NotImplementedError("Escribe este test")


def test_alerta_cuando_un_valor_fuera_aunque_resto_optimo():
    # si co2 es 1500 pero temperatura y humedad son óptimas → alerta
    raise NotImplementedError("Escribe este test")


def test_co2_negativo_lanza_excepcion():
    raise NotImplementedError("Escribe este test")


def test_humedad_mayor_de_100_lanza_excepcion():
    raise NotImplementedError("Escribe este test")
