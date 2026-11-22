"""Quick Sort (divide y vencerás) con partición de Lomuto.

Se usa en el Laboratorio de algoritmos para comparar su eficiencia con la de
Merge Sort (ver ``analisis.py``). Se implementa a mano, sin ``sorted()`` ni
``list.sort()``.

Estrategia
----------
1. Se elige como pivote el último elemento de la sublista.
2. Partición: los elementos menores que el pivote pasan a su izquierda y el
   pivote queda en su posición final.
3. Se ordenan recursivamente las dos sublistas a cada lado del pivote.

Complejidad
-----------
* Tiempo: promedio y mejor caso O(n log n); peor caso O(n²), que con este pivote
  ocurre cuando la entrada ya está ordenada (o en orden inverso): cada partición
  separa un solo elemento, así que se hacen (n-1) + (n-2) + ... + 1 = n(n-1)/2
  comparaciones.
* Espacio: O(log n) de pila en promedio y O(n) en el peor caso; ordena en el
  mismo arreglo (sobre una copia), sin listas auxiliares.
* No es estable: elementos con clave igual pueden cambiar de orden.

Recursión: la profundidad llega a n-1 en el peor caso, por eso el laboratorio
limita el tamaño de las entradas.

Este módulo es lógica pura: no depende de Flask ni de la base de datos.
"""
from dataclasses import dataclass


@dataclass
class ResultadoQuickSort:
    """Lista ordenada y evidencias de que el algoritmo se ejecutó."""

    elementos: list
    comparaciones: int = 0
    # Niveles anidados de recursión en los que se parte una sublista de 2 o más
    # elementos (equivale a ``profundidad_maxima`` de Merge Sort).
    profundidad_maxima: int = 0
    particiones: int = 0


def quick_sort(elementos, clave=None):
    """Ordena ``elementos`` de menor a mayor según ``clave``.

    No modifica la lista recibida: trabaja sobre una copia.
    """
    clave = clave or (lambda elemento: elemento)
    datos = list(elementos)
    resultado = ResultadoQuickSort(elementos=datos)
    _ordenar(datos, 0, len(datos) - 1, 1, clave, resultado)
    return resultado


def _ordenar(datos, bajo, alto, nivel, clave, resultado):
    """Divide: particiona y ordena recursivamente cada lado del pivote."""
    if bajo >= alto:  # caso base: 0 o 1 elementos ya están ordenados
        return
    if nivel > resultado.profundidad_maxima:
        resultado.profundidad_maxima = nivel

    posicion_pivote = _particionar(datos, bajo, alto, clave, resultado)
    _ordenar(datos, bajo, posicion_pivote - 1, nivel + 1, clave, resultado)
    _ordenar(datos, posicion_pivote + 1, alto, nivel + 1, clave, resultado)


def _particionar(datos, bajo, alto, clave, resultado):
    """Partición de Lomuto: deja el pivote en su posición final y la devuelve."""
    resultado.particiones += 1
    pivote = clave(datos[alto])
    frontera = bajo  # los elementos de bajo..frontera-1 son menores que el pivote
    for actual in range(bajo, alto):
        resultado.comparaciones += 1
        if clave(datos[actual]) < pivote:
            datos[frontera], datos[actual] = datos[actual], datos[frontera]
            frontera += 1
    datos[frontera], datos[alto] = datos[alto], datos[frontera]
    return frontera
