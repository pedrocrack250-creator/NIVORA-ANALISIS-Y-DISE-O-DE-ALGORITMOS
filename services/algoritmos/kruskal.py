"""Árbol de expansión mínima mediante el algoritmo de Kruskal."""
from services.algoritmos.union_find import UnionFind


def kruskal(vertices, aristas):
    """Devuelve (aristas_elegidas, costo_total, pasos).

    Cada arista tiene la forma (origen, destino, peso). El grafo debe ser
    conexo para producir un árbol de expansión mínima.
    """
    vertices = list(vertices)
    if not vertices:
        return [], 0, []
    uf = UnionFind(vertices)
    elegidas, pasos, costo = [], [], 0
    for origen, destino, peso in sorted(aristas, key=lambda arista: arista[2]):
        if origen not in uf.padre or destino not in uf.padre:
            raise ValueError("Todas las aristas deben usar vértices declarados")
        if uf.union(origen, destino):
            elegidas.append((origen, destino, peso))
            costo += peso
            decision = "aceptada"
        else:
            decision = "descartada: formaría un ciclo"
        pasos.append({"arista": (origen, destino, peso), "decision": decision})
        if len(elegidas) == len(vertices) - 1:
            break
    if len(elegidas) != len(vertices) - 1:
        raise ValueError("El grafo no es conexo; no existe un árbol de expansión mínima")
    return elegidas, costo, pasos
