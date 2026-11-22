"""Análisis de eficiencia de algoritmos: medir, comparar y verificar recurrencias.

En lugar de cronometrar (el tiempo depende de la máquina), se CUENTAN las
operaciones que realmente ejecutan los algoritmos de Nivora y se comparan con
las cotas teóricas:

* Merge Sort y Quick Sort (``merge_sort.py`` y ``quick_sort.py``): comparaciones
  en el caso promedio y en el peor caso.
* Escaleras sin memoización (``programacion_dinamica.py``): llamadas recursivas.

Las relaciones de recurrencia que describen esos conteos se resuelven aquí y se
verifican contra las mediciones reales.

Este módulo es lógica pura: no depende de Flask ni de la base de datos.
"""
import math
import random

from services.algoritmos.merge_sort import merge_sort
from services.algoritmos.programacion_dinamica import (
    escaleras_memoizado,
    escaleras_recursivo,
    escaleras_tabulado,
)
from services.algoritmos.quick_sort import quick_sort

N_MINIMO = 2
# Quick Sort recorre hasta n-1 niveles de recursión en su peor caso: el tope
# mantiene la pila lejos del límite de recursión de Python.
N_MAXIMO = 256
TAMANOS_TABLA = (8, 16, 32, 64, 128, 256)
SEMILLA = 7  # entrada "aleatoria" reproducible: mismos números en cada visita

CASOS = {
    "aleatorio": "Aleatorio (caso promedio)",
    "ordenado": "Ya ordenado",
    "inverso": "Orden inverso",
}


# --- Entradas -------------------------------------------------------------------

def validar_tamano(valor):
    """Convierte ``valor`` a entero y comprueba el rango permitido."""
    mensaje = f"Escribe un número entero entre {N_MINIMO} y {N_MAXIMO}."
    if isinstance(valor, bool):
        raise ValueError(mensaje)
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ValueError(mensaje) from None
    if not N_MINIMO <= n <= N_MAXIMO:
        raise ValueError(mensaje)
    return n


def validar_caso(valor):
    if valor not in CASOS:
        raise ValueError("Elige uno de los casos disponibles.")
    return valor


def generar_entrada(n, caso):
    """Permutación de 0..n-1 según el caso (sin elementos repetidos)."""
    if caso == "ordenado":
        return list(range(n))
    if caso == "inverso":
        return list(range(n - 1, -1, -1))
    datos = list(range(n))
    random.Random(SEMILLA).shuffle(datos)
    return datos


# --- Cotas teóricas -------------------------------------------------------------

def cota_n_log_n(n):
    """n·⌈log2 n⌉: cota del trabajo de Merge Sort."""
    return n * math.ceil(math.log2(n))


def cota_cuadratica(n):
    """n(n-1)/2: comparaciones de Quick Sort en su peor caso."""
    return n * (n - 1) // 2


# --- Medición de ordenamiento ---------------------------------------------------

def medir_ordenamiento(n, caso):
    """Ejecuta Merge Sort y Quick Sort con la misma entrada y cuenta su trabajo."""
    entrada = generar_entrada(n, validar_caso(caso))
    esperado = list(range(n))
    merge = merge_sort(entrada)
    quick = quick_sort(entrada)
    if merge.elementos != esperado or quick.elementos != esperado:
        raise AssertionError("Un algoritmo de ordenamiento devolvió un resultado incorrecto")
    return {
        "n": n,
        "caso": caso,
        "merge_comparaciones": merge.comparaciones,
        "merge_profundidad": merge.profundidad_maxima,
        "quick_comparaciones": quick.comparaciones,
        "quick_profundidad": quick.profundidad_maxima,
        "cota_n_log_n": cota_n_log_n(n),
        "cota_cuadratica": cota_cuadratica(n),
    }


def tabla_ordenamiento(tamanos=TAMANOS_TABLA):
    """Una fila por tamaño con las mediciones de cada caso."""
    return [
        {"n": n, **{caso: medir_ordenamiento(n, caso) for caso in CASOS}}
        for n in tamanos
    ]


def medir_espacio(n):
    """Memoria auxiliar observada (niveles de recursión y celdas guardadas)."""
    aleatorio = medir_ordenamiento(n, "aleatorio")
    ordenado = medir_ordenamiento(n, "ordenado")
    return {
        "n": n,
        "merge_profundidad": aleatorio["merge_profundidad"],
        "quick_profundidad_aleatorio": aleatorio["quick_profundidad"],
        "quick_profundidad_ordenado": ordenado["quick_profundidad"],
        "memo_entradas": len(escaleras_memoizado(n).memo),
        "tabla_entradas": len(escaleras_tabulado(n).tabla),
    }


# --- Relaciones de recurrencia ----------------------------------------------------

def recurrencia_merge_sort(n):
    """C(n) = C(⌊n/2⌋) + C(⌈n/2⌉) + (n - 1),  C(1) = 0.

    Comparaciones de Merge Sort en el peor caso: cada fusión de n elementos
    necesita como máximo n-1 comparaciones. Se resuelve por tabulación.
    """
    valores = {1: 0}
    for k in range(2, n + 1):
        valores[k] = valores[k // 2] + valores[k - k // 2] + (k - 1)
    return valores[n]


def recurrencia_quick_sort_peor(n):
    """Q(n) = Q(n - 1) + (n - 1),  Q(1) = 0  →  n(n-1)/2.

    Peor caso: el pivote separa un solo elemento, así que cada partición cuesta
    n-1 comparaciones y deja un subproblema de tamaño n-1.
    """
    total = 0
    for k in range(2, n + 1):
        total += k - 1
    return total


def recurrencia_escaleras_llamadas(n):
    """L(n) = L(n - 1) + L(n - 2) + 1,  L(0) = L(1) = 1.

    Llamadas de la recursión pura de las escaleras: la propia llamada más las de
    los dos subproblemas.
    """
    valores = [1, 1]
    for k in range(2, n + 1):
        valores.append(valores[k - 1] + valores[k - 2] + 1)
    return valores[n]


PHI = (1 + math.sqrt(5)) / 2  # raíz positiva de x² = x + 1


def verificar_recurrencias():
    """Compara cada recurrencia con el conteo real del algoritmo correspondiente."""
    merge = []
    for n in (8, 16, 32, 64, 128):
        medido = medir_ordenamiento(n, "aleatorio")["merge_comparaciones"]
        recurrencia = recurrencia_merge_sort(n)
        merge.append({"n": n, "medido": medido, "recurrencia": recurrencia,
                      "cota": cota_n_log_n(n), "cumple": medido <= recurrencia <= cota_n_log_n(n)})

    quick = []
    for n in (8, 16, 32, 64, 128):
        medido = medir_ordenamiento(n, "ordenado")["quick_comparaciones"]
        recurrencia = recurrencia_quick_sort_peor(n)
        quick.append({"n": n, "medido": medido, "recurrencia": recurrencia,
                      "cumple": medido == recurrencia})

    escaleras = []
    for n in (5, 10, 15, 20, 25):
        medido = escaleras_recursivo(n)[1]
        recurrencia = recurrencia_escaleras_llamadas(n)
        escaleras.append({
            "n": n, "medido": medido, "recurrencia": recurrencia,
            "razon": recurrencia / recurrencia_escaleras_llamadas(n - 1),
            "cumple": medido == recurrencia,
        })
    return {"merge": merge, "quick": quick, "escaleras": escaleras, "phi": PHI}


# --- Teorema maestro ----------------------------------------------------------------

def _monomio(exponente, con_log=False):
    """Formatea Θ(n^exponente) (con log n si corresponde)."""
    if exponente == 0:
        base = ""
    elif math.isclose(exponente, round(exponente)):
        base = {1: "n", 2: "n²", 3: "n³"}.get(round(exponente), f"n^{round(exponente)}")
    else:
        base = f"n^{exponente:.2f}"
    if con_log:
        base = f"{base} log n" if base else "log n"
    return f"Θ({base or '1'})"


def teorema_maestro(a, b, d):
    """Resuelve T(n) = a·T(n/b) + Θ(n^d) con a ≥ 1, b > 1, d ≥ 0.

    Compara el trabajo de las hojas, n^(log_b a), con el de combinar, n^d:
    * a > b^d → domina el trabajo de las hojas:      Θ(n^(log_b a))   (caso 1)
    * a = b^d → todos los niveles pesan igual:       Θ(n^d log n)     (caso 2)
    * a < b^d → domina el trabajo de combinar:       Θ(n^d)           (caso 3)
    """
    if a < 1 or b <= 1 or d < 0:
        raise ValueError("Se requiere a ≥ 1, b > 1 y d ≥ 0.")
    peso_combinar = b ** d
    if math.isclose(a, peso_combinar):
        caso, resultado = 2, _monomio(d, con_log=True)
    elif a > peso_combinar:
        caso, resultado = 1, _monomio(math.log(a, b))
    else:
        caso, resultado = 3, _monomio(d)
    return {"a": a, "b": b, "d": d, "caso": caso, "resultado": resultado,
            "exponente_hojas": math.log(a, b)}


EJEMPLOS_MAESTRO = (
    (2, 2, 1, "Merge Sort (y Quick Sort en el caso promedio)"),
    (1, 2, 0, "Búsqueda binaria"),
    (4, 2, 1, "4 subproblemas de la mitad del tamaño y trabajo lineal"),
    (1, 2, 1, "Un subproblema de la mitad y trabajo lineal"),
)


def ejemplos_maestro():
    return [{**teorema_maestro(a, b, d), "descripcion": texto}
            for a, b, d, texto in EJEMPLOS_MAESTRO]
