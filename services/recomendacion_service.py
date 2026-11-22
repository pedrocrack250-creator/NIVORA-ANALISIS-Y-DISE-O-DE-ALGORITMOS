"""Recomendación de la siguiente pregunta para el estudiante.

Aplica el algoritmo voraz de ``services.algoritmos.voraz`` con el progreso real
(intentos, aciertos y errores por pregunta guardados en ``PROGRESO_EJERCICIO``),
pero solo sobre las preguntas de lecciones que el estudiante ya puede abrir:
nunca se recomienda algo bloqueado por la ruta de aprendizaje.
"""
from services import progreso_service
from services.algoritmos.voraz import recomendar_siguiente


def _motivo(pregunta):
    errores = int(pregunta.get("errores", 0))
    if errores:
        veces = "vez" if errores == 1 else "veces"
        return f"La respondiste mal {errores} {veces}: conviene reforzarla."
    return "Es la siguiente pregunta pendiente de tu ruta."


def siguiente_pregunta(preguntas, unidades, lecciones, actividades):
    """Devuelve la pregunta recomendada (con su ``motivo``) o ``None``.

    ``preguntas``: salida de ``ExerciseRepository.find_quiz_questions``.
    ``unidades`` / ``lecciones``: ruta de aprendizaje (``RutaModel``).
    ``actividades``: progreso por lección del estudiante (sesión).
    """
    accesibles = {
        lesson["id"] for lesson in lecciones
        if progreso_service.leccion_desbloqueada(unidades, lecciones, lesson, actividades)
    }
    elegida = recomendar_siguiente(
        [pregunta for pregunta in preguntas if pregunta["lesson_id"] in accesibles]
    )
    if elegida is None:
        return None
    return {**elegida, "motivo": _motivo(elegida)}
