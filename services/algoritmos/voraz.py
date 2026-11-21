"""Recomendación voraz de preguntas pendientes según el progreso real."""

DIFICULTAD = {"basico": 1, "intermedio": 2, "avanzado": 3}


def prioridad(ejercicio):
    """Tupla de prioridad de una pregunta: la menor tupla es la más urgente.

    Orden de criterios: más errores acumulados, menor dificultad, menor
    posición dentro de la lección y menor ID (desempate determinista).
    """
    return (
        -int(ejercicio.get("errores", 0)),
        DIFICULTAD.get(str(ejercicio.get("dificultad", "basico")).lower(), 99),
        int(ejercicio.get("numero", 0)),
        int(ejercicio.get("id_ejercicio", 0)),
    )


def pendientes(ejercicios):
    """Preguntas que el estudiante todavía no ha respondido correctamente."""
    return [e for e in ejercicios if e.get("estado") != "correcto"]


def recomendar_siguiente(ejercicios):
    """Elige una pregunta pendiente usando una prioridad local y determinista.

    Estrategia voraz: en una sola pasada se conserva siempre el mejor candidato
    visto hasta el momento, sin reconsiderar decisiones ni planear la secuencia.
    Prioridad: ver ``prioridad``.
    Cada elemento debe incluir estado, errores, dificultad, numero e id_ejercicio.
    Devuelve None cuando no hay preguntas pendientes.

    Complejidad: tiempo O(n) (filtrar y comparar cada pendiente una vez);
    espacio O(n) por la lista de pendientes.
    """
    candidatos = pendientes(ejercicios)
    if not candidatos:
        return None

    return min(candidatos, key=prioridad)
