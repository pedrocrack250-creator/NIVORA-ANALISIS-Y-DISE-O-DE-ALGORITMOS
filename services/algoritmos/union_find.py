"""Estructura Union-Find (conjuntos disjuntos) para detectar ciclos."""

class UnionFind:
    def __init__(self, elementos):
        self.padre = {elemento: elemento for elemento in elementos}
        self.rango = {elemento: 0 for elemento in elementos}

    def find(self, elemento):
        if elemento not in self.padre:
            raise ValueError(f"Elemento desconocido: {elemento}")
        if self.padre[elemento] != elemento:
            self.padre[elemento] = self.find(self.padre[elemento])
        return self.padre[elemento]

    def union(self, a, b):
        raiz_a, raiz_b = self.find(a), self.find(b)
        if raiz_a == raiz_b:
            return False
        if self.rango[raiz_a] < self.rango[raiz_b]:
            raiz_a, raiz_b = raiz_b, raiz_a
        self.padre[raiz_b] = raiz_a
        if self.rango[raiz_a] == self.rango[raiz_b]:
            self.rango[raiz_a] += 1
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)
