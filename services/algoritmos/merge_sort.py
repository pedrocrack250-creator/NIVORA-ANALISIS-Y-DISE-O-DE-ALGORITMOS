"""Merge Sort implementado manualmente (divide y vencerás).

Se usa en Nivora para ordenar los ejercicios del módulo Practicar.
No se emplea ``sorted()`` ni ``list.sort()``: el orden resulta de dividir
recursivamente la lista y combinar las mitades ya ordenadas.

Complejidad
-----------
* Tiempo:  O(n log n) en el mejor, promedio y peor caso. La lista se divide
  log2(n) veces y cada nivel de la recursión combina n elementos.
* Espacio: O(n) auxiliar (listas temporales de la combinación) más O(log n)
  de pila de recursión.
* Estable: ante claves iguales se conserva el orden original (se usa ``<=``).

Este módulo es lógica pura: no depende de Flask ni de la base de datos.
"""
from dataclasses import dataclass, field

RANGO_DIFICULTAD = {"basico": 1, "intermedio": 2, "avanzado": 3}
SIN_RANGO = len(RANGO_DIFICULTAD) + 1  # dificultades desconocidas van al final


@dataclass
class ResultadoMergeSort:
    """Lista ordenada y evidencias de que el algoritmo se ejecutó."""

    elementos: list
    comparaciones: int = 0
    profundidad_maxima: int = 0
    fusiones: list = field(default_factory=list)


def merge_sort(elementos, clave=None, etiqueta=None):
    """Ordena ``elementos`` de menor a mayor según ``clave``.

    No modifica la lista recibida. ``etiqueta`` solo sirve para describir las
    fusiones en el rastro (``fusiones``); no influye en el orden.
    """
    clave = clave or (lambda elemento: elemento)
    etiqueta = etiqueta or (lambda elemento: str(clave(elemento)))
    resultado = ResultadoMergeSort(elementos=[])
    resultado.elementos = _dividir(list(elementos), clave, etiqueta, 0, resultado)
    return resultado


def _dividir(lista, clave, etiqueta, nivel, resultado):
    """Divide: parte la lista por la mitad hasta llegar al caso base."""
    if nivel > resultado.profundidad_maxima:
        resultado.profundidad_maxima = nivel

    if len(lista) <= 1:  # caso base: una lista de 0 o 1 elementos ya está ordenada
        return lista

    medio = len(lista) // 2
    izquierda = _dividir(lista[:medio], clave, etiqueta, nivel + 1, resultado)
    derecha = _dividir(lista[medio:], clave, etiqueta, nivel + 1, resultado)
    return _combinar(izquierda, derecha, clave, etiqueta, nivel, resultado)


def _combinar(izquierda, derecha, clave, etiqueta, nivel, resultado):
    """Vence: mezcla dos listas ya ordenadas en una sola lista ordenada."""
    combinada = []
    i = j = 0
    while i < len(izquierda) and j < len(derecha):
        resultado.comparaciones += 1
        if clave(izquierda[i]) <= clave(derecha[j]):  # <= conserva la estabilidad
            combinada.append(izquierda[i])
            i += 1
        else:
            combinada.append(derecha[j])
            j += 1
    combinada.extend(izquierda[i:])
    combinada.extend(derecha[j:])

    resultado.fusiones.append({
        "nivel": nivel,
        "izquierda": [etiqueta(e) for e in izquierda],
        "derecha": [etiqueta(e) for e in derecha],
        "resultado": [etiqueta(e) for e in combinada],
    })
    return combinada


# --- Aplicación en Nivora: ordenar ejercicios --------------------------------

def _clave_dificultad(ejercicio):
    rango = RANGO_DIFICULTAD.get(ejercicio["dificultad"], SIN_RANGO)
    return (rango, ejercicio["id_unidad"], ejercicio["id_ejercicio"])


def _clave_posicion(ejercicio):
    return (ejercicio["id_unidad"], ejercicio["id_ejercicio"])


CRITERIOS = {
    "dificultad": ("Dificultad", _clave_dificultad),
    "posicion": ("Posición en la ruta", _clave_posicion),
}


def ordenar_ejercicios(ejercicios, criterio="dificultad"):
    """Ordena ejercicios (diccionarios) con Merge Sort según un criterio."""
    if criterio not in CRITERIOS:
        raise ValueError(f"Criterio de orden no válido: {criterio}")
    _nombre, clave = CRITERIOS[criterio]
    return merge_sort(
        ejercicios,
        clave=clave,
        etiqueta=lambda ejercicio: f"#{ejercicio['id_ejercicio']}",
    )
