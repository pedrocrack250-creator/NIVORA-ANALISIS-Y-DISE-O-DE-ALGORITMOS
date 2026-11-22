"""Programación dinámica: problema de las escaleras.

Problema: una escalera tiene ``n`` escalones y se puede subir de 1 o de 2
escalones por vez. ¿De cuántas formas distintas se puede llegar arriba?

    formas(n) = formas(n - 1) + formas(n - 2)      con formas(0) = formas(1) = 1

El mismo subproblema aparece muchas veces (subproblemas superpuestos): para
calcular formas(5) se calcula formas(3) dos veces, formas(2) tres veces, etc.

Se implementan tres soluciones que se EJECUTAN de verdad:

* ``escaleras_recursivo``: recursión pura, recalcula todo.
    Tiempo O(2^n) (exactamente 2*formas(n) - 1 llamadas), espacio O(n) de pila.
* ``escaleras_memoizado``: recursión + diccionario (memoización).
    Cada estado se calcula una sola vez y luego se reutiliza.
    Tiempo O(n) (2n - 1 llamadas), espacio O(n) (diccionario + pila).
* ``escaleras_tabulado``: tabulación (programación dinámica ascendente).
    Se llena una tabla desde los casos base hasta n, sin recursión.
    Tiempo O(n) (n - 1 sumas), espacio O(n) (la tabla; O(1) si solo se
    guardan los dos últimos valores).

Este módulo es lógica pura: no depende de Flask ni de la base de datos.
"""
from dataclasses import dataclass, field
from time import perf_counter

N_MINIMO = 0
# La versión sin memoización hace ~242 785 llamadas con n = 25; se limita para
# que la comparación real se ejecute en una fracción de segundo.
N_MAXIMO = 25


def validar_n(valor):
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


def escaleras_recursivo(n):
    """Recursión pura. Devuelve ``(formas, llamadas)``."""
    llamadas = 0

    def formas(k):
        nonlocal llamadas
        llamadas += 1
        if k <= 1:  # caso base
            return 1
        return formas(k - 1) + formas(k - 2)

    return formas(n), llamadas


@dataclass
class ResultadoMemoizado:
    formas: int
    llamadas: int
    reutilizaciones: int
    memo: dict = field(default_factory=dict)          # estado -> valor
    veces_reutilizado: dict = field(default_factory=dict)  # estado -> reutilizaciones
    eventos: list = field(default_factory=list)       # secuencia de decisiones


def escaleras_memoizado(n):
    """Recursión con memoización (programación dinámica descendente)."""
    resultado = ResultadoMemoizado(formas=0, llamadas=0, reutilizaciones=0)
    memo = resultado.memo

    def formas(k):
        resultado.llamadas += 1
        if k in memo:  # subproblema ya resuelto: se reutiliza sin recalcular
            resultado.reutilizaciones += 1
            resultado.veces_reutilizado[k] = resultado.veces_reutilizado.get(k, 0) + 1
            resultado.eventos.append({"n": k, "accion": "reutilizado", "valor": memo[k]})
            return memo[k]
        if k <= 1:  # caso base
            valor = 1
        else:
            valor = formas(k - 1) + formas(k - 2)
        memo[k] = valor  # se guarda para no volver a calcularlo
        resultado.eventos.append({"n": k, "accion": "calculado", "valor": valor})
        return valor

    resultado.formas = formas(n)
    return resultado


@dataclass
class ResultadoTabulado:
    formas: int
    operaciones: int  # sumas realizadas: una por cada estado desde 2 hasta n
    tabla: list = field(default_factory=list)  # tabla[k] = formas(k)


def escaleras_tabulado(n):
    """Tabulación: se llena la tabla de abajo hacia arriba (sin recursión)."""
    tabla = [1] * (n + 1)  # casos base: formas(0) = formas(1) = 1
    operaciones = 0
    for k in range(2, n + 1):
        tabla[k] = tabla[k - 1] + tabla[k - 2]  # solo usa estados ya calculados
        operaciones += 1
    return ResultadoTabulado(formas=tabla[n], operaciones=operaciones, tabla=tabla)


@dataclass
class ComparacionEscaleras:
    n: int
    formas: int
    llamadas_recursivo: int
    llamadas_memoizado: int
    reutilizaciones: int
    tiempo_recursivo_ms: float
    tiempo_memoizado_ms: float
    estados: list  # [{"n", "valor", "reutilizaciones"}] de la tabla de memoización
    eventos: list
    operaciones_tabulado: int = 0
    tiempo_tabulado_ms: float = 0.0
    tabla: list = field(default_factory=list)  # tabla de la solución tabulada

    @property
    def llamadas_evitadas(self):
        return self.llamadas_recursivo - self.llamadas_memoizado

    @property
    def factor_llamadas(self):
        return self.llamadas_recursivo / self.llamadas_memoizado


def comparar_escaleras(n):
    """Ejecuta ambas soluciones con el mismo ``n`` y compara su trabajo real."""
    n = validar_n(n)

    inicio = perf_counter()
    formas_recursivo, llamadas_recursivo = escaleras_recursivo(n)
    tiempo_recursivo = (perf_counter() - inicio) * 1000

    inicio = perf_counter()
    memoizado = escaleras_memoizado(n)
    tiempo_memoizado = (perf_counter() - inicio) * 1000

    inicio = perf_counter()
    tabulado = escaleras_tabulado(n)
    tiempo_tabulado = (perf_counter() - inicio) * 1000

    if not formas_recursivo == memoizado.formas == tabulado.formas:  # deben coincidir siempre
        raise AssertionError("Las soluciones no coinciden")

    estados = [
        {
            "n": estado,
            "valor": memoizado.memo[estado],
            "reutilizaciones": memoizado.veces_reutilizado.get(estado, 0),
        }
        for estado in range(n + 1)
    ]
    return ComparacionEscaleras(
        n=n,
        formas=memoizado.formas,
        llamadas_recursivo=llamadas_recursivo,
        llamadas_memoizado=memoizado.llamadas,
        reutilizaciones=memoizado.reutilizaciones,
        tiempo_recursivo_ms=tiempo_recursivo,
        tiempo_memoizado_ms=tiempo_memoizado,
        estados=estados,
        eventos=memoizado.eventos,
        operaciones_tabulado=tabulado.operaciones,
        tiempo_tabulado_ms=tiempo_tabulado,
        tabla=tabulado.tabla,
    )
