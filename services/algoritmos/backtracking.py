"""Backtracking: problema de las N reinas (en Nivora, el tablero de 4 x 4).

Problema: ubicar N reinas en un tablero N x N sin que ninguna ataque a otra
(misma columna o misma diagonal; la fila se evita colocando una reina por fila).

Estrategia (backtracking):
  1. Se avanza fila por fila.
  2. En cada fila se prueban las columnas de izquierda a derecha.
  3. Si la posición es segura, se coloca la reina y se pasa a la fila siguiente.
  4. Si la posición tiene conflicto, se descarta (poda) sin explorar lo que
     vendría después.
  5. Si ninguna columna sirve, se retrocede: se retira la reina anterior y se
     prueba su siguiente columna.
  Caso base: se llegó a la fila N, es decir, hay N reinas válidas.

Complejidad
-----------
* Tiempo: O(N!) en el peor caso. Sin poda habría N^N tableros completos
  (256 para N = 4); la poda descarta ramas enteras en cuanto aparece un conflicto.
* Espacio: O(N) (lista de columnas y pila de recursión), sin contar el rastro
  de eventos que se guarda solo para poder mostrar el proceso.

Este módulo es lógica pura: no depende de Flask ni de la base de datos.
"""
from dataclasses import dataclass, field

N_MINIMO = 1
N_MAXIMO = 8


def conflicto_reina(columnas, fila, columna):
    """Indica si una reina en (fila, columna) sería atacada por las ya colocadas.

    ``columnas[f]`` es la columna de la reina de la fila ``f``. Devuelve
    ``None`` si la posición es segura o ``(motivo, fila_atacante)`` si no.
    """
    for fila_previa, columna_previa in enumerate(columnas):
        if columna_previa == columna:
            return "columna", fila_previa
        if abs(columna_previa - columna) == abs(fila_previa - fila):
            return "diagonal", fila_previa
    return None


@dataclass
class ResultadoReinas:
    n: int
    numero_solucion: int
    solucion: list = None  # columnas[f] de la solución pedida, o None si no existe
    soluciones_encontradas: int = 0
    intentos: int = 0
    conflictos: int = 0  # ramas podadas
    colocaciones: int = 0
    retrocesos: int = 0
    eventos: list = field(default_factory=list)

    @property
    def combinaciones_sin_poda(self):
        return self.n ** self.n


def resolver_reinas(n=4, numero_solucion=1):
    """Busca la solución número ``numero_solucion`` y registra cada decisión."""
    if not N_MINIMO <= n <= N_MAXIMO:
        raise ValueError(f"El tablero debe tener entre {N_MINIMO} y {N_MAXIMO} filas.")
    if numero_solucion < 1:
        raise ValueError("El número de solución debe ser al menos 1.")

    resultado = ResultadoReinas(n=n, numero_solucion=numero_solucion)
    columnas = []

    def registrar(accion, fila, columna, mensaje, conflicto_con=None, motivo=None):
        resultado.eventos.append({
            "accion": accion,
            "fila": fila,
            "columna": columna,
            "tablero": list(columnas),  # estado del tablero tras el evento
            "conflicto_con": conflicto_con,
            "motivo": motivo,
            "mensaje": mensaje,
        })

    def colocar(fila):
        """Devuelve True cuando ya se alcanzó la solución pedida."""
        if fila == n:  # caso base: n reinas colocadas sin conflictos
            resultado.soluciones_encontradas += 1
            resultado.solucion = list(columnas)
            registrar(
                "solucion", None, None,
                f"¡Solución {resultado.soluciones_encontradas}! Las {n} reinas están a salvo.",
            )
            return resultado.soluciones_encontradas == numero_solucion

        for columna in range(n):
            resultado.intentos += 1
            registrar(
                "intentar", fila, columna,
                f"Fila {fila + 1}: se intenta la columna {columna + 1}.",
            )
            conflicto = conflicto_reina(columnas, fila, columna)
            if conflicto:  # poda: esta rama no puede llevar a una solución
                motivo, fila_atacante = conflicto
                resultado.conflictos += 1
                registrar(
                    "conflicto", fila, columna,
                    f"Conflicto en {motivo} con la reina de la fila {fila_atacante + 1}: se descarta.",
                    conflicto_con=[fila_atacante, columnas[fila_atacante]],
                    motivo=motivo,
                )
                continue

            columnas.append(columna)
            resultado.colocaciones += 1
            registrar(
                "colocar", fila, columna,
                f"Posición segura: se coloca la reina en fila {fila + 1}, columna {columna + 1}.",
            )
            if colocar(fila + 1):
                return True

            columnas.pop()  # retroceso: se deshace la decisión
            resultado.retrocesos += 1
            registrar(
                "retroceder", fila, columna,
                f"Retroceso: se retira la reina de fila {fila + 1}, columna {columna + 1}.",
            )

        registrar(
            "agotada", fila, None,
            f"Fila {fila + 1}: no quedan columnas por probar."
            + (" Se vuelve a la fila anterior." if fila > 0 else " No hay más soluciones."),
        )
        return False

    colocar(0)
    if resultado.soluciones_encontradas < numero_solucion:
        resultado.solucion = None
    return resultado
