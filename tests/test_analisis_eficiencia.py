"""Quick Sort, tabulación, recurrencias, teorema maestro y la página de análisis."""
import math
import random

import pytest

from app import create_app
from config import TestingConfig
from services.algoritmos import analisis
from services.algoritmos.merge_sort import merge_sort
from services.algoritmos.programacion_dinamica import (
    comparar_escaleras,
    escaleras_memoizado,
    escaleras_recursivo,
    escaleras_tabulado,
)
from services.algoritmos.quick_sort import quick_sort


# --- Quick Sort ------------------------------------------------------------------

def test_quick_sort_casos_basicos():
    assert quick_sort([]).elementos == []
    assert quick_sort([7]).elementos == [7]
    assert quick_sort([5, 2, 9, 1, 5, 6, 0]).elementos == [0, 1, 2, 5, 5, 6, 9]
    assert quick_sort([3, 1, 3, 1, 2, 2]).elementos == [1, 1, 2, 2, 3, 3]


def test_quick_sort_coincide_con_el_orden_de_referencia():
    azar = random.Random(5)
    for _ in range(100):
        datos = [azar.randint(-20, 20) for _ in range(azar.randint(0, 50))]
        assert quick_sort(datos).elementos == sorted(datos)  # sorted solo como oráculo de la prueba


def test_quick_sort_acepta_clave_y_no_modifica_la_entrada():
    original = [("b", 2), ("a", 3), ("c", 1)]
    assert quick_sort(original, clave=lambda par: par[1]).elementos == [("c", 1), ("b", 2), ("a", 3)]
    assert original == [("b", 2), ("a", 3), ("c", 1)]


@pytest.mark.parametrize("n", [2, 8, 64, 200])
@pytest.mark.parametrize("construir", [lambda n: list(range(n)), lambda n: list(range(n - 1, -1, -1))])
def test_quick_sort_peor_caso_exacto(n, construir):
    resultado = quick_sort(construir(n))
    assert resultado.comparaciones == n * (n - 1) // 2   # O(n²)
    assert resultado.profundidad_maxima == n - 1          # pila O(n)


def test_quick_sort_promedio_es_mucho_menor_que_el_peor_caso():
    datos = analisis.generar_entrada(256, "aleatorio")
    resultado = quick_sort(datos)
    assert resultado.comparaciones < analisis.cota_cuadratica(256) / 5
    assert resultado.profundidad_maxima < 40


def test_quick_sort_cuenta_particiones():
    assert quick_sort([2, 1]).particiones == 1
    assert quick_sort([1]).particiones == 0


# --- Tabulación ----------------------------------------------------------------------

@pytest.mark.parametrize("n,esperado", [(0, 1), (1, 1), (2, 2), (5, 8), (10, 89), (25, 121393)])
def test_tabulacion_resultados_conocidos(n, esperado):
    assert escaleras_tabulado(n).formas == esperado


def test_tabulacion_coincide_con_recursion_y_memoizacion():
    for n in range(0, 26):
        assert escaleras_tabulado(n).formas == escaleras_recursivo(n)[0] == escaleras_memoizado(n).formas


def test_tabulacion_hace_n_menos_1_sumas_y_guarda_n_mas_1_celdas():
    for n in range(2, 26):
        resultado = escaleras_tabulado(n)
        assert resultado.operaciones == n - 1
        assert len(resultado.tabla) == n + 1
    assert escaleras_tabulado(0).operaciones == 0 and escaleras_tabulado(1).operaciones == 0


def test_comparacion_incluye_tabulacion():
    comparacion = comparar_escaleras(10)
    assert comparacion.operaciones_tabulado == 9
    assert comparacion.tabla[-1] == comparacion.formas == 89


# --- Recurrencias ---------------------------------------------------------------------

def test_recurrencia_de_escaleras_coincide_con_las_llamadas_reales():
    for n in range(0, 21):
        assert analisis.recurrencia_escaleras_llamadas(n) == escaleras_recursivo(n)[1]


def test_recurrencia_de_quick_sort_coincide_con_lo_medido_en_el_peor_caso():
    for n in (2, 5, 16, 100):
        assert analisis.recurrencia_quick_sort_peor(n) == quick_sort(list(range(n))).comparaciones == n * (n - 1) // 2


def test_recurrencia_de_merge_sort_acota_lo_medido_y_es_menor_que_n_log_n():
    azar = random.Random(3)
    for n in (2, 3, 7, 16, 33, 100, 256):
        datos = list(range(n))
        azar.shuffle(datos)
        medido = merge_sort(datos).comparaciones
        recurrencia = analisis.recurrencia_merge_sort(n)
        assert medido <= recurrencia <= analisis.cota_n_log_n(n)


def test_recurrencia_de_merge_sort_forma_cerrada_en_potencias_de_2():
    for k in range(1, 9):
        n = 2 ** k
        assert analisis.recurrencia_merge_sort(n) == (k - 1) * n + 1


def test_razon_de_llamadas_tiende_a_la_razon_aurea():
    razon = analisis.recurrencia_escaleras_llamadas(25) / analisis.recurrencia_escaleras_llamadas(24)
    assert math.isclose(razon, analisis.PHI, abs_tol=1e-4)


def test_verificar_recurrencias_todas_cumplen():
    resultado = analisis.verificar_recurrencias()
    for clave in ("merge", "quick", "escaleras"):
        assert resultado[clave] and all(fila["cumple"] for fila in resultado[clave])


# --- Teorema maestro ------------------------------------------------------------------

@pytest.mark.parametrize("a,b,d,caso,resultado", [
    (2, 2, 1, 2, "Θ(n log n)"),   # Merge Sort
    (1, 2, 0, 2, "Θ(log n)"),     # búsqueda binaria
    (4, 2, 1, 1, "Θ(n²)"),
    (1, 2, 1, 3, "Θ(n)"),
    (8, 2, 2, 1, "Θ(n³)"),
    (3, 2, 1, 1, "Θ(n^1.58)"),
    (2, 2, 2, 3, "Θ(n²)"),
])
def test_teorema_maestro(a, b, d, caso, resultado):
    respuesta = analisis.teorema_maestro(a, b, d)
    assert (respuesta["caso"], respuesta["resultado"]) == (caso, resultado)


@pytest.mark.parametrize("a,b,d", [(0, 2, 1), (2, 1, 1), (2, 0.5, 1), (2, 2, -1)])
def test_teorema_maestro_rechaza_parametros_invalidos(a, b, d):
    with pytest.raises(ValueError):
        analisis.teorema_maestro(a, b, d)


# --- Mediciones ---------------------------------------------------------------------------

@pytest.mark.parametrize("valor", [1, 0, -5, analisis.N_MAXIMO + 1, "abc", "", "2.5", None, True])
def test_validar_tamano_rechaza_valores_invalidos(valor):
    with pytest.raises(ValueError):
        analisis.validar_tamano(valor)


def test_validar_tamano_acepta_los_limites():
    assert analisis.validar_tamano(" 2 ") == 2 and analisis.validar_tamano("256") == 256


def test_validar_caso():
    assert analisis.validar_caso("inverso") == "inverso"
    with pytest.raises(ValueError):
        analisis.validar_caso("raro")


def test_entradas_son_permutaciones_y_el_caso_aleatorio_es_reproducible():
    for caso in analisis.CASOS:
        assert merge_sort(analisis.generar_entrada(30, caso)).elementos == list(range(30))
    assert analisis.generar_entrada(30, "aleatorio") == analisis.generar_entrada(30, "aleatorio")
    assert analisis.generar_entrada(30, "aleatorio") != list(range(30))


def test_medicion_respeta_las_cotas_teoricas():
    for n in (2, 5, 16, 100, 256):
        for caso in analisis.CASOS:
            fila = analisis.medir_ordenamiento(n, caso)
            assert fila["merge_comparaciones"] <= analisis.cota_n_log_n(n)
            assert fila["quick_comparaciones"] <= analisis.cota_cuadratica(n)
            assert fila["merge_profundidad"] == math.ceil(math.log2(n))


def test_merge_sort_es_mejor_que_quick_sort_en_listas_ordenadas():
    fila = analisis.medir_ordenamiento(128, "ordenado")
    assert fila["quick_comparaciones"] == analisis.cota_cuadratica(128)
    # En una lista ordenada cada fusión gasta tantas comparaciones como elementos tiene
    # su mitad izquierda: (n/2)·log2 n en total para n potencia de 2.
    assert fila["merge_comparaciones"] == 128 // 2 * 7 == 448
    assert fila["quick_comparaciones"] > 15 * fila["merge_comparaciones"]


def test_tabla_ordenamiento_tiene_un_caso_por_columna():
    tabla = analisis.tabla_ordenamiento((8, 16))
    assert [fila["n"] for fila in tabla] == [8, 16]
    assert set(tabla[0]) == {"n", *analisis.CASOS}


def test_medicion_de_espacio():
    espacio = analisis.medir_espacio(64)
    assert espacio["merge_profundidad"] == 6
    assert espacio["quick_profundidad_ordenado"] == 63
    assert espacio["quick_profundidad_aleatorio"] < espacio["quick_profundidad_ordenado"]
    assert espacio["memo_entradas"] == espacio["tabla_entradas"] == 65


# --- Página ----------------------------------------------------------------------------------

@pytest.fixture
def cliente():
    return create_app(TestingConfig).test_client()


def iniciar_sesion(cliente):
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        sesion["usuario"] = {"id_persona": 1, "nombre": "Ana"}


def test_pagina_requiere_login(cliente):
    respuesta = cliente.get("/aprender/laboratorio/eficiencia")
    assert respuesta.status_code == 302 and respuesta.headers["Location"].endswith("/login")


def test_pagina_muestra_mediciones_recurrencias_y_codigo(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/aprender/laboratorio/eficiencia?n=64")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "Merge Sort vs. Quick Sort con n = 64" in html
    assert "<strong>2016</strong>" in html                      # n(n-1)/2 para n = 64
    assert "<td>2016</td>" in html                              # Quick Sort ordenada, peor caso
    assert "Θ(n log n)" in html and "Θ(n²)" in html
    assert "def _particionar" in html                           # código real mostrado
    assert "✗" not in html                                      # todas las verificaciones cumplen
    assert html.count("✓") >= 15


def test_pagina_usa_n_por_defecto_y_rechaza_valores_invalidos(cliente):
    iniciar_sesion(cliente)
    assert "n = 64" in cliente.get("/aprender/laboratorio/eficiencia").get_data(as_text=True)
    for valor in ("1", "999", "abc"):
        respuesta = cliente.get(f"/aprender/laboratorio/eficiencia?n={valor}")
        assert respuesta.status_code == 400
        assert "entre 2 y 256" in respuesta.get_data(as_text=True)


def test_pagina_de_escaleras_muestra_la_tabulacion(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender/laboratorio/programacion-dinamica?n=10").get_data(as_text=True)
    assert "Tabulación (iterativa)" in html and "9 sumas" in html
    assert "Memoización vs. tabulación" in html and "1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89" in html


def test_la_actividad_aparece_en_aprender(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "/aprender/laboratorio/eficiencia" in html
