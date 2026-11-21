import math
import random

import pytest

from app import create_app
from config import TestingConfig
from services.algoritmos.merge_sort import (
    CRITERIOS,
    merge_sort,
    ordenar_ejercicios,
)


def ej(id_ejercicio, dificultad, id_unidad=1):
    return {"id_ejercicio": id_ejercicio, "dificultad": dificultad, "id_unidad": id_unidad}


# --- Algoritmo -----------------------------------------------------------

def test_lista_vacia():
    resultado = merge_sort([])
    assert resultado.elementos == []
    assert resultado.comparaciones == 0
    assert resultado.fusiones == []


def test_un_elemento():
    resultado = merge_sort([7])
    assert resultado.elementos == [7]
    assert resultado.comparaciones == 0


def test_lista_desordenada():
    assert merge_sort([5, 2, 9, 1, 5, 6, 0]).elementos == [0, 1, 2, 5, 5, 6, 9]


def test_elementos_repetidos():
    assert merge_sort([3, 1, 3, 1, 2, 2]).elementos == [1, 1, 2, 2, 3, 3]


def test_ya_ordenada_e_inversa():
    assert merge_sort([1, 2, 3, 4]).elementos == [1, 2, 3, 4]
    assert merge_sort([4, 3, 2, 1]).elementos == [1, 2, 3, 4]


def test_no_modifica_la_lista_original():
    original = [3, 1, 2]
    merge_sort(original)
    assert original == [3, 1, 2]


def test_es_estable():
    datos = [("b", 1), ("a", 1), ("c", 0), ("d", 1)]
    resultado = merge_sort(datos, clave=lambda par: par[1])
    assert resultado.elementos == [("c", 0), ("b", 1), ("a", 1), ("d", 1)]


def test_coincide_con_orden_de_referencia_en_listas_aleatorias():
    azar = random.Random(42)
    for _ in range(50):
        datos = [azar.randint(-20, 20) for _ in range(azar.randint(0, 40))]
        assert merge_sort(datos).elementos == sorted(datos)  # sorted solo como oráculo de la prueba


def test_comparaciones_y_profundidad_respetan_n_log_n():
    n = 64
    datos = list(range(n, 0, -1))
    resultado = merge_sort(datos)
    assert resultado.comparaciones <= n * math.ceil(math.log2(n))
    assert resultado.profundidad_maxima == math.ceil(math.log2(n))
    assert len(resultado.fusiones) == n - 1  # una fusión por cada par de mitades


def test_rastro_de_fusiones_describe_el_proceso():
    resultado = merge_sort([3, 1, 2])
    ultima = resultado.fusiones[-1]
    assert ultima["nivel"] == 0
    assert ultima["resultado"] == ["1", "2", "3"]


# --- Aplicación a ejercicios ---------------------------------------------

def test_ordena_por_diferentes_dificultades():
    ejercicios = [
        ej(1, "avanzado"), ej(2, "basico"), ej(3, "intermedio"),
        ej(4, "basico"), ej(5, "avanzado"),
    ]
    resultado = ordenar_ejercicios(ejercicios, "dificultad")
    assert [e["id_ejercicio"] for e in resultado.elementos] == [2, 4, 3, 1, 5]


def test_ordena_por_posicion_en_la_ruta():
    ejercicios = [ej(5, "basico", 2), ej(2, "basico", 3), ej(9, "basico", 1), ej(1, "basico", 2)]
    resultado = ordenar_ejercicios(ejercicios, "posicion")
    assert [e["id_ejercicio"] for e in resultado.elementos] == [9, 1, 5, 2]


def test_dificultad_desconocida_va_al_final():
    resultado = ordenar_ejercicios([ej(1, "raro"), ej(2, "avanzado"), ej(3, "basico")])
    assert [e["id_ejercicio"] for e in resultado.elementos] == [3, 2, 1]


def test_criterio_invalido_lanza_error():
    with pytest.raises(ValueError):
        ordenar_ejercicios([], "inexistente")


def test_orden_final_esta_ordenado_segun_la_clave():
    azar = random.Random(7)
    dificultades = ["basico", "intermedio", "avanzado"]
    ejercicios = [ej(i, azar.choice(dificultades), azar.randint(1, 4)) for i in range(1, 30)]
    for criterio, (_nombre, clave) in CRITERIOS.items():
        claves = [clave(e) for e in ordenar_ejercicios(ejercicios, criterio).elementos]
        assert all(a <= b for a, b in zip(claves, claves[1:]))


# --- Integración con Practicar (BD temporal) ------------------------------

@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "test.db"))
    cliente = create_app(TestingConfig).test_client()
    return cliente


def iniciar_sesion(cliente):
    with cliente.session_transaction() as sesion:
        sesion["usuario"] = {"id_persona": 1, "nombre": "Ana"}


def test_ruta_requiere_login(cliente):
    respuesta = cliente.get("/aprender/laboratorio/merge-sort")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/login")


def test_ruta_muestra_ejercicios_ordenados_por_dificultad(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender/laboratorio/merge-sort?orden=dificultad")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "Merge Sort" in html
    assert "comparaciones" in html
    # el ejercicio avanzado #16 aparece después del básico #13
    assert html.index("Factorial recursivo") > html.index("Saludo personalizado")
    assert html.index("Factorial recursivo") > html.index("Contar vocales")


def test_el_orden_cambia_segun_el_criterio(cliente):
    iniciar_sesion(cliente)
    por_dificultad = cliente.get("/aprender/laboratorio/merge-sort?orden=dificultad").get_data(as_text=True)
    por_posicion = cliente.get("/aprender/laboratorio/merge-sort?orden=posicion").get_data(as_text=True)
    # por posición (unidad 2) "Palíndromo" va antes que "Promedio de una lista" (unidad 3)
    assert por_posicion.index("Palíndromo") < por_posicion.index("Promedio de una lista")
    # por dificultad "Promedio" (intermedio) va antes que "Palíndromo" (avanzado)
    assert por_dificultad.index("Promedio de una lista") < por_dificultad.index("Palíndromo")


def test_criterio_desconocido_usa_dificultad(cliente):
    iniciar_sesion(cliente)
    assert cliente.get("/aprender/laboratorio/merge-sort?orden=xyz").status_code == 200


def test_aprender_enlaza_a_ejercicios_y_la_url_antigua_redirige(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender")
    assert respuesta.status_code == 200
    assert b"/aprender/laboratorio/merge-sort" in respuesta.data
    antigua = cliente.get("/practica/ejercicios?orden=posicion")
    assert antigua.status_code == 301
    assert antigua.headers["Location"].endswith("/aprender/laboratorio/merge-sort?orden=posicion")


# --- Visualización paso a paso ----------------------------------------------

import json
import re

from services.algoritmos.merge_sort import rastro_merge_sort, validar_arreglo


def test_rastro_coincide_con_merge_sort():
    for numeros in ([38, 27, 43, 3, 9, 82, 10], [5, 2, 4, 1], [8, 3, 5, 3, 1], [2, 1]):
        rastro = rastro_merge_sort(numeros)
        esperado = merge_sort(numeros)
        assert rastro["ordenado"] == esperado.elementos == sorted(numeros)
        assert rastro["comparaciones"] == esperado.comparaciones
        assert rastro["eventos"][-1]["comparaciones"] == esperado.comparaciones


def test_rastro_muestra_dividir_caso_base_y_combinar_en_orden():
    eventos = rastro_merge_sort([5, 2, 4, 1])["eventos"]
    acciones = [evento["accion"] for evento in eventos]
    assert acciones[0] == "inicio" and acciones[-1] == "fin"
    assert acciones[1:4] == ["dividir", "dividir", "base"]
    assert acciones.count("dividir") == 3 and acciones.count("base") == 4
    assert "comparar" in acciones and "combinado" in acciones
    # cada nodo ocupa exactamente el tramo del arreglo del que salió
    final = eventos[-1]["nodos"]
    assert final[0]["valores"] == [1, 2, 4, 5] and final[0]["estado"] == "ordenado"
    for nodo in final:
        assert nodo["fin"] - nodo["inicio"] == len(nodo["valores"])


def test_rastro_explica_cada_comparacion():
    eventos = rastro_merge_sort([3, 1])["eventos"]
    comparacion = next(e for e in eventos if e["accion"] == "comparar")
    assert comparacion["mensaje"] == "Comparamos 3 y 1: 1 es menor, así que 1 pasa al resultado."
    assert {m["tipo"] for m in comparacion["marcas"]} == {"comparado", "elegido", "nuevo"}


@pytest.mark.parametrize("texto", ["1", "a, b", "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11", "1, 5000"])
def test_validar_arreglo_rechaza_entradas_invalidas(texto):
    with pytest.raises(ValueError):
        validar_arreglo(texto)


def test_validar_arreglo_acepta_comas_y_espacios():
    assert validar_arreglo("5, 2  -3,7") == [5, 2, -3, 7]


def test_pagina_incluye_la_visualizacion_paso_a_paso(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender/laboratorio/merge-sort?arreglo=5,2,4,1").get_data(as_text=True)
    assert 'id="msort-arbol"' in html
    assert "js/laboratorio/merge_sort.js" in html
    assert "Cómo funciona" in html and "def _combinar" in html
    datos = json.loads(re.search(r'id="msort-datos">(.*?)</script>', html, re.S).group(1))
    assert datos["n"] == 4
    assert datos["eventos"] == rastro_merge_sort([5, 2, 4, 1])["eventos"]
    assert "[5, 2, 4, 1] → [1, 2, 4, 5]" in html
    assert cliente.get("/static/js/laboratorio/merge_sort.js").status_code == 200


def test_pagina_rechaza_arreglo_invalido_sin_romperse(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender/laboratorio/merge-sort?arreglo=hola")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "números enteros" in html
    assert "[3, 9, 10, 27, 38, 43, 82]" in html  # se muestra el ejemplo inicial
