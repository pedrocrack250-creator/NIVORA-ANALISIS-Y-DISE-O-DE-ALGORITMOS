import json
import re

import pytest

from app import create_app
from config import TestingConfig
from services.algoritmos.backtracking import (
    N_MAXIMO,
    conflicto_reina,
    resolver_reinas,
)

SOLUCIONES_4 = [[1, 3, 0, 2], [2, 0, 3, 1]]


def sin_ataques(columnas):
    """Comprobación independiente: ninguna pareja comparte columna ni diagonal."""
    for i in range(len(columnas)):
        for j in range(i + 1, len(columnas)):
            if columnas[i] == columnas[j] or abs(columnas[i] - columnas[j]) == j - i:
                return False
    return True


# --- Restricciones ----------------------------------------------------------

def test_posicion_segura_no_tiene_conflicto():
    assert conflicto_reina([], 0, 0) is None
    assert conflicto_reina([0], 1, 2) is None


def test_detecta_conflicto_de_columna_y_de_diagonal():
    assert conflicto_reina([1], 1, 1) == ("columna", 0)
    assert conflicto_reina([1], 1, 2) == ("diagonal", 0)
    assert conflicto_reina([1], 1, 0) == ("diagonal", 0)
    assert conflicto_reina([0, 2], 2, 0) == ("columna", 0)


# --- Solución de las 4 reinas -------------------------------------------------

def test_encuentra_una_solucion_valida():
    resultado = resolver_reinas(4)
    assert resultado.solucion == [1, 3, 0, 2]
    assert sin_ataques(resultado.solucion)


def test_hay_exactamente_cuatro_reinas_en_filas_y_columnas_distintas():
    solucion = resolver_reinas(4).solucion
    assert len(solucion) == 4
    assert sorted(solucion) == [0, 1, 2, 3]  # una reina por fila y por columna


def test_el_tablero_de_4x4_tiene_exactamente_dos_soluciones():
    primera = resolver_reinas(4, 1)
    segunda = resolver_reinas(4, 2)
    assert [primera.solucion, segunda.solucion] == SOLUCIONES_4
    assert all(sin_ataques(s) for s in (primera.solucion, segunda.solucion))
    tercera = resolver_reinas(4, 3)
    assert tercera.solucion is None
    assert tercera.soluciones_encontradas == 2


@pytest.mark.parametrize("n,cantidad", [(1, 1), (2, 0), (3, 0), (4, 2), (5, 10), (6, 4), (7, 40), (8, 92)])
def test_cantidad_de_soluciones_coincide_con_los_valores_conocidos(n, cantidad):
    assert resolver_reinas(n, 10**6).soluciones_encontradas == cantidad


def test_sin_solucion_para_2_y_3_reinas():
    for n in (2, 3):
        resultado = resolver_reinas(n)
        assert resultado.solucion is None
        assert resultado.eventos[-1]["accion"] == "agotada"


@pytest.mark.parametrize("n", [0, -1, N_MAXIMO + 1])
def test_tamano_invalido(n):
    with pytest.raises(ValueError):
        resolver_reinas(n)


def test_numero_de_solucion_invalido():
    with pytest.raises(ValueError):
        resolver_reinas(4, 0)


# --- Comportamiento de los retrocesos y la poda ------------------------------

def test_hay_retrocesos_en_las_4_reinas():
    resultado = resolver_reinas(4)
    assert resultado.retrocesos == 4
    assert resultado.conflictos == 18
    assert sum(e["accion"] == "retroceder" for e in resultado.eventos) == resultado.retrocesos


def test_el_rastro_se_comporta_como_una_pila():
    """Reproduce los eventos: colocar apila, retroceder desapila la última reina."""
    pila = []
    for evento in resolver_reinas(4, 2).eventos:
        if evento["accion"] == "colocar":
            pila.append(evento["columna"])
        elif evento["accion"] == "retroceder":
            assert pila.pop() == evento["columna"]  # se deshace la última decisión
        assert evento["tablero"] == pila


def test_reinas_en_el_tablero_al_final_son_colocaciones_menos_retrocesos():
    resultado = resolver_reinas(4)
    assert resultado.colocaciones - resultado.retrocesos == 4


def test_nunca_se_coloca_una_reina_en_conflicto():
    for numero in (1, 2):
        for evento in resolver_reinas(4, numero).eventos:
            assert sin_ataques(evento["tablero"])


def test_cada_conflicto_es_un_ataque_real_y_se_poda():
    eventos = resolver_reinas(4).eventos
    for i, evento in enumerate(eventos):
        if evento["accion"] != "conflicto":
            continue
        fila, columna = evento["fila"], evento["columna"]
        fila_atacante, columna_atacante = evento["conflicto_con"]
        assert evento["tablero"][fila_atacante] == columna_atacante
        if evento["motivo"] == "columna":
            assert columna_atacante == columna
        else:
            assert abs(columna_atacante - columna) == abs(fila_atacante - fila)
        # poda: tras un conflicto no se avanza a la fila siguiente desde esa posición
        assert eventos[i + 1]["fila"] == fila
        assert eventos[i + 1]["accion"] in ("intentar", "agotada")


def test_caso_base_solo_con_n_reinas():
    eventos = resolver_reinas(4, 2).eventos
    soluciones = [e for e in eventos if e["accion"] == "solucion"]
    assert len(soluciones) == 2
    assert all(len(e["tablero"]) == 4 for e in soluciones)
    assert eventos[-1]["accion"] == "solucion"  # el rastro termina al hallar la pedida


def test_la_poda_reduce_el_trabajo():
    resultado = resolver_reinas(4)
    assert resultado.colocaciones < resultado.combinaciones_sin_poda
    assert resultado.combinaciones_sin_poda == 256
    assert resultado.intentos == 26


def test_es_determinista():
    assert resolver_reinas(4, 2).eventos == resolver_reinas(4, 2).eventos


# --- Integración con Flask --------------------------------------------------

@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "test.db"))
    return create_app(TestingConfig).test_client()


def iniciar_sesion(cliente):
    with cliente.session_transaction() as sesion:
        sesion["usuario"] = {"id_persona": 1, "nombre": "Ana"}


def datos_del_rastro(html):
    contenido = re.search(r'id="reinas-datos">(.*?)</script>', html, re.S).group(1)
    return json.loads(contenido)


def test_ruta_requiere_login(cliente):
    respuesta = cliente.get("/aprender/laboratorio/backtracking")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/login")


def test_pagina_entrega_el_rastro_real_del_algoritmo(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender/laboratorio/backtracking")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'id="tablero"' in html
    assert "js/laboratorio/backtracking.js" in html
    assert "def resolver_reinas" in html  # código real mostrado
    datos = datos_del_rastro(html)
    esperado = resolver_reinas(4, 1)
    assert datos["n"] == 4
    assert datos["eventos"] == esperado.eventos
    assert datos["eventos"][-1]["tablero"] == [1, 3, 0, 2]


def test_pagina_permite_ver_la_segunda_solucion(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender/laboratorio/backtracking?solucion=2").get_data(as_text=True)
    assert datos_del_rastro(html)["eventos"][-1]["tablero"] == [2, 0, 3, 1]


@pytest.mark.parametrize("valor", ["3", "0", "x"])
def test_solucion_invalida_devuelve_400_y_muestra_la_primera(cliente, valor):
    iniciar_sesion(cliente)
    respuesta = cliente.get(f"/aprender/laboratorio/backtracking?solucion={valor}")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "solución 1 o la solución 2" in html
    assert datos_del_rastro(html)["eventos"][-1]["tablero"] == [1, 3, 0, 2]


def test_indice_y_javascript_estan_disponibles(cliente):
    iniciar_sesion(cliente)
    assert "/aprender/laboratorio/backtracking" in cliente.get("/aprender").get_data(as_text=True)
    assert cliente.get("/static/js/laboratorio/backtracking.js").status_code == 200
