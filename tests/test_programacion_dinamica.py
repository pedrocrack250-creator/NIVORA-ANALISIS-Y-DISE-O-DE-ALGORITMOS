import pytest

from app import create_app
from config import TestingConfig
from services.algoritmos.programacion_dinamica import (
    N_MAXIMO,
    comparar_escaleras,
    escaleras_memoizado,
    escaleras_recursivo,
    validar_n,
)

# formas(n) = Fibonacci(n + 1): 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89 ...
CONOCIDOS = {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 8, 6: 13, 10: 89, 20: 10946, 25: 121393}


# --- Resultados conocidos y valores límite ---------------------------------

@pytest.mark.parametrize("n,esperado", list(CONOCIDOS.items()))
def test_resultados_conocidos_en_ambas_soluciones(n, esperado):
    assert escaleras_recursivo(n)[0] == esperado
    assert escaleras_memoizado(n).formas == esperado


def test_valores_pequenos_y_limite_inferior():
    assert escaleras_memoizado(0).formas == 1
    assert escaleras_memoizado(0).llamadas == 1
    assert escaleras_memoizado(1).formas == 1


def test_valor_limite_superior():
    assert N_MAXIMO == 25
    assert comparar_escaleras(N_MAXIMO).formas == 121393


def test_ambas_soluciones_coinciden_en_todo_el_rango():
    for n in range(0, 21):
        assert escaleras_recursivo(n)[0] == escaleras_memoizado(n).formas


# --- Validación de entrada --------------------------------------------------

@pytest.mark.parametrize("valor", [-1, N_MAXIMO + 1, 1000, "abc", "", "1.5", None, True])
def test_validar_n_rechaza_valores_invalidos(valor):
    with pytest.raises(ValueError):
        validar_n(valor)


def test_validar_n_acepta_texto_numerico():
    assert validar_n(" 7 ") == 7
    assert validar_n("0") == 0
    assert validar_n(25) == 25


# --- Reutilización de subproblemas -----------------------------------------

def test_llamadas_sin_memoizacion_crecen_como_2_formas_menos_1():
    for n in range(0, 21):
        formas, llamadas = escaleras_recursivo(n)
        assert llamadas == 2 * formas - 1


def test_llamadas_con_memoizacion_son_lineales():
    for n in range(1, 26):
        assert escaleras_memoizado(n).llamadas == 2 * n - 1


def test_reutilizaciones_y_estados_guardados():
    resultado = escaleras_memoizado(10)
    assert resultado.reutilizaciones == 8  # n - 2 resultados reutilizados
    assert sorted(resultado.memo) == list(range(11))  # n + 1 estados distintos
    # cada estado de 1 a n-2 se reutiliza exactamente una vez; el resto, ninguna
    assert {k: v for k, v in resultado.veces_reutilizado.items()} == {k: 1 for k in range(1, 9)}


def test_eventos_registran_calculos_y_reutilizaciones():
    resultado = escaleras_memoizado(5)
    acciones = [evento["accion"] for evento in resultado.eventos]
    assert acciones.count("calculado") == 6   # estados 0..5
    assert acciones.count("reutilizado") == 3
    assert resultado.eventos[-1] == {"n": 5, "accion": "calculado", "valor": 8}
    # un estado reutilizado ya había sido calculado antes
    vistos = set()
    for evento in resultado.eventos:
        if evento["accion"] == "reutilizado":
            assert evento["n"] in vistos
        else:
            vistos.add(evento["n"])


def test_memoizacion_no_comparte_estado_entre_ejecuciones():
    primera = escaleras_memoizado(12)
    segunda = escaleras_memoizado(12)
    assert primera.llamadas == segunda.llamadas == 23
    assert primera.memo is not segunda.memo


# --- Comparación recursivo vs optimizado -----------------------------------

def test_comparacion_muestra_la_optimizacion_real():
    c = comparar_escaleras(25)
    assert c.llamadas_recursivo == 242785
    assert c.llamadas_memoizado == 49
    assert c.llamadas_evitadas == 242785 - 49
    assert c.factor_llamadas > 4000
    assert len(c.estados) == 26
    assert c.tiempo_recursivo_ms >= 0 and c.tiempo_memoizado_ms >= 0


def test_comparacion_valida_la_entrada():
    with pytest.raises(ValueError):
        comparar_escaleras(26)


# --- Integración con Flask --------------------------------------------------

@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "test.db"))
    return create_app(TestingConfig).test_client()


def iniciar_sesion(cliente):
    with cliente.session_transaction() as sesion:
        sesion["usuario"] = {"id_persona": 1, "nombre": "Ana"}


def test_rutas_del_laboratorio_requieren_login(cliente):
    for ruta in ("/aprender/laboratorio", "/aprender/laboratorio/programacion-dinamica"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 302
        assert respuesta.headers["Location"].endswith("/login")


def test_indice_del_laboratorio_lista_las_actividades(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "Algoritmos interactivos" in html
    assert "/aprender/laboratorio/merge-sort" in html
    assert "/aprender/laboratorio/programacion-dinamica" in html


def test_pagina_calcula_con_el_valor_ingresado(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender/laboratorio/programacion-dinamica?n=10")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "hay 89 formas" in html
    assert "memoización" in html
    assert "def formas(k):" in html  # se muestra el código real que se ejecutó


def test_pagina_con_valor_inicial_por_defecto(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender/laboratorio/programacion-dinamica")
    assert respuesta.status_code == 200
    assert "hay 34 formas" in respuesta.get_data(as_text=True)  # n = 8


@pytest.mark.parametrize("n", ["99", "-3", "abc"])
def test_pagina_rechaza_valores_invalidos_sin_romperse(cliente, n):
    iniciar_sesion(cliente)
    respuesta = cliente.get(f"/aprender/laboratorio/programacion-dinamica?n={n}")
    assert respuesta.status_code == 400
    assert "entre 0 y 25" in respuesta.get_data(as_text=True)


def test_aprender_enlaza_al_laboratorio(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert 'id="laboratorio"' in html
    assert "/aprender/laboratorio/programacion-dinamica" in html
