"""Árbol de expansión mínima mediante el algoritmo de Prim."""
import heapq


def prim(vertices, aristas, inicio=None):
    """Devuelve (aristas_elegidas, costo_total, pasos) para un grafo no dirigido."""
    vertices = list(vertices)
    if not vertices:
        return [], 0, []
    if inicio is None:
        inicio = vertices[0]
    if inicio not in vertices:
        raise ValueError("El vértice inicial no pertenece al grafo")

    adyacencia = {v: [] for v in vertices}
    for a, b, peso in aristas:
        if a not in adyacencia or b not in adyacencia:
            raise ValueError("Todas las aristas deben usar vértices declarados")
        adyacencia[a].append((peso, b, a))
        adyacencia[b].append((peso, a, b))

    visitados = {inicio}
    frontera = []
    for peso, vecino, origen in adyacencia[inicio]:
        heapq.heappush(frontera, (peso, origen, vecino))

    elegidas, pasos, costo = [], [], 0
    while frontera and len(visitados) < len(vertices):
        peso, origen, destino = heapq.heappop(frontera)
        if destino in visitados:
            pasos.append({"arista": (origen, destino, peso), "decision": "descartada: destino ya conectado"})
            continue
        visitados.add(destino)
        elegidas.append((origen, destino, peso))
        costo += peso
        pasos.append({"arista": (origen, destino, peso), "decision": "aceptada"})
        for nuevo_peso, vecino, _actual in adyacencia[destino]:
            if vecino not in visitados:
                heapq.heappush(frontera, (nuevo_peso, destino, vecino))

    if len(visitados) != len(vertices):
        raise ValueError("El grafo no es conexo; no existe un árbol de expansión mínima")
    return elegidas, costo, pasos
