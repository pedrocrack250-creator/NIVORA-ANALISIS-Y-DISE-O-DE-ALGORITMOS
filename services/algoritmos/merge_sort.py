"""Merge Sort implementado manualmente (divide y vencerás).

Se usa en Nivora para ordenar los ejercicios del Laboratorio de algoritmos
y para generar la visualización paso a paso de la lección.
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


# --- Visualización paso a paso ------------------------------------------------

ARREGLO_EJEMPLO = [38, 27, 43, 3, 9, 82, 10]
TAMANO_MINIMO, TAMANO_MAXIMO = 2, 10
VALOR_MINIMO, VALOR_MAXIMO = -999, 999


def validar_arreglo(texto):
    """Convierte "5, 2, 9" en [5, 2, 9]; lanza ValueError con un mensaje claro."""
    partes = [parte for parte in str(texto).replace(",", " ").split() if parte]
    try:
        numeros = [int(parte) for parte in partes]
    except ValueError:
        raise ValueError("Escribe solo números enteros separados por comas.") from None
    if not TAMANO_MINIMO <= len(numeros) <= TAMANO_MAXIMO:
        raise ValueError(
            f"Escribe entre {TAMANO_MINIMO} y {TAMANO_MAXIMO} números separados por comas."
        )
    if any(not VALOR_MINIMO <= numero <= VALOR_MAXIMO for numero in numeros):
        raise ValueError(f"Usa números entre {VALOR_MINIMO} y {VALOR_MAXIMO}.")
    return numeros


def _texto(lista):
    return "[" + ", ".join(str(valor) for valor in lista) + "]"


def rastro_merge_sort(numeros):
    """Ejecuta Merge Sort sobre ``numeros`` y registra cada paso.

    Sigue exactamente el mismo esquema que ``_dividir`` y ``_combinar``: partir
    por la mitad hasta el caso base y mezclar comparando el primer elemento
    pendiente de cada mitad. Cada evento guarda una fotografía completa de los
    bloques visibles para que la página solo tenga que dibujarla.

    Devuelve ``{"arreglo", "ordenado", "comparaciones", "niveles", "eventos"}``.
    """
    nodos = {}       # id -> {id, nivel, inicio, fin, valores, estado}
    orden = []       # ids en orden de aparición (para dibujar de forma estable)
    eventos = []
    contador = {"comparaciones": 0, "niveles": 0}

    def crear(nivel, inicio, fin, valores, estado):
        identificador = len(orden)
        nodos[identificador] = {"id": identificador, "nivel": nivel, "inicio": inicio,
                                "fin": fin, "valores": list(valores), "estado": estado}
        orden.append(identificador)
        contador["niveles"] = max(contador["niveles"], nivel + 1)
        return identificador

    def registrar(accion, mensaje, marcas=()):
        eventos.append({
            "accion": accion,
            "mensaje": mensaje,
            "comparaciones": contador["comparaciones"],
            "nodos": [dict(nodos[i], valores=list(nodos[i]["valores"])) for i in orden],
            "marcas": [{"nodo": nodo, "indice": indice, "tipo": tipo} for nodo, indice, tipo in marcas],
        })

    def ordenar(identificador):
        nodo = nodos[identificador]
        lista = nodo["valores"]
        if len(lista) <= 1:
            nodo["estado"] = "ordenado"
            registrar("base", f"{_texto(lista)} tiene un solo elemento: ya está ordenado (caso base).")
            return lista

        # 1. Dividir
        medio = len(lista) // 2
        nodo["estado"] = "dividido"
        izquierda_id = crear(nodo["nivel"] + 1, nodo["inicio"], nodo["inicio"] + medio,
                             lista[:medio], "pendiente")
        derecha_id = crear(nodo["nivel"] + 1, nodo["inicio"] + medio, nodo["fin"],
                           lista[medio:], "pendiente")
        registrar("dividir", f"Dividimos {_texto(lista)} por la mitad: "
                             f"{_texto(lista[:medio])} y {_texto(lista[medio:])}.")

        # 2. Ordenar cada mitad (primero la izquierda, luego la derecha)
        izquierda = ordenar(izquierda_id)
        derecha = ordenar(derecha_id)

        # 3. Combinar
        nodo["estado"] = "combinando"
        nodo["valores"] = []
        registrar("combinar", f"Las dos mitades ya están ordenadas. Combinamos "
                              f"{_texto(izquierda)} y {_texto(derecha)} en una sola lista.")
        i = j = 0
        while i < len(izquierda) and j < len(derecha):
            contador["comparaciones"] += 1
            a, b = izquierda[i], derecha[j]
            if a <= b:  # <= conserva el orden original ante empates (estable)
                nodo["valores"].append(a)
                marcas = [(izquierda_id, i, "elegido"), (derecha_id, j, "comparado")]
                mensaje = (f"Comparamos {a} y {b}: {a} es menor o igual, "
                           f"así que {a} pasa al resultado.")
                i += 1
            else:
                nodo["valores"].append(b)
                marcas = [(izquierda_id, i, "comparado"), (derecha_id, j, "elegido")]
                mensaje = f"Comparamos {a} y {b}: {b} es menor, así que {b} pasa al resultado."
                j += 1
            marcas += [(identificador, len(nodo["valores"]) - 1, "nuevo")]
            registrar("comparar", mensaje, marcas)

        resto, lado, lado_id, desde = (
            (izquierda[i:], "derecha", izquierda_id, i) if i < len(izquierda)
            else (derecha[j:], "izquierda", derecha_id, j)
        )
        if resto:
            inicio_resto = len(nodo["valores"])
            nodo["valores"].extend(resto)
            marcas = [(lado_id, desde + k, "elegido") for k in range(len(resto))]
            marcas += [(identificador, inicio_resto + k, "nuevo") for k in range(len(resto))]
            registrar("resto", f"La mitad {lado} ya no tiene elementos. Copiamos lo que queda, "
                               f"{_texto(resto)}, que ya está en orden.", marcas)

        nodos[izquierda_id]["estado"] = "usado"
        nodos[derecha_id]["estado"] = "usado"
        nodo["estado"] = "ordenado"
        registrar("combinado", f"Resultado de la combinación: {_texto(nodo['valores'])}.")
        return nodo["valores"]

    raiz = crear(0, 0, len(numeros), numeros, "pendiente")
    registrar("inicio", f"Arreglo original: {_texto(numeros)}. "
                        "Pulsa «Siguiente» para empezar a dividirlo.")
    ordenado = ordenar(raiz)
    eventos[-1]["accion"] = "fin"
    eventos[-1]["mensaje"] = (f"¡Listo! El arreglo ordenado es {_texto(ordenado)}, "
                              f"tras {contador['comparaciones']} comparaciones.")
    return {
        "arreglo": list(numeros),
        "ordenado": ordenado,
        "comparaciones": contador["comparaciones"],
        "niveles": contador["niveles"],
        "eventos": eventos,
    }


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
