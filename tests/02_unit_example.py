import pytest

# Ejecutar: pytest 02_unit_example.py -v


def calcular_nota(puntuacion: float) -> str:
    if not (0 <= puntuacion <= 10):
        raise ValueError(f"Puntuación fuera de rango: {puntuacion}")

    if puntuacion < 5:
        return "Suspenso"
    elif puntuacion < 7:
        return "Aprobado"
    elif puntuacion < 9:
        return "Notable"
    else:
        return "Sobresaliente"


def test_suspenso():
    assert calcular_nota(3.0) == "Suspenso"


def test_aprobado():
    assert calcular_nota(6.0) == "Aprobado"


def test_notable():
    assert calcular_nota(8.0) == "Notable"


def test_sobresaliente():
    assert calcular_nota(10.0) == "Sobresaliente"


def test_limite_suspenso_aprobado():
    # 5.0 exacto debe ser Aprobado, no Suspenso
    assert calcular_nota(4.9) == "Suspenso"
    assert calcular_nota(5.0) == "Aprobado"


def test_limite_aprobado_notable():
    assert calcular_nota(6.9) == "Aprobado"
    assert calcular_nota(7.0) == "Notable"


def test_limite_notable_sobresaliente():
    assert calcular_nota(8.9) == "Notable"
    assert calcular_nota(9.0) == "Sobresaliente"


def test_puntuacion_cero_es_suspenso():
    assert calcular_nota(0.0) == "Suspenso"


def test_puntuacion_negativa_lanza_excepcion():
    with pytest.raises(ValueError):
        calcular_nota(-1)


def test_puntuacion_mayor_de_diez_lanza_excepcion():
    with pytest.raises(ValueError):
        calcular_nota(11)
