"""Reglas de progreso y desbloqueo de la ruta de aprendizaje.

Única fuente de verdad para decidir cuándo una lección está completada,
cuándo una unidad está terminada y qué unidades o lecciones están
desbloqueadas. Trabaja con los registros del usuario (`PROGRESO_LECCION`,
cargados en la sesión al iniciar sesión y actualizados en cada quiz), por lo
que no depende de contadores mostrados en pantalla.
"""


def actividad(actividades, lesson_id):
    """Normaliza el registro de una lección (dict o valor heredado bool)."""
    data = (actividades or {}).get(lesson_id)
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    return {"completada": bool(data), "intentada": bool(data), "iniciada": bool(data)}


def leccion_completada(actividades, lesson_id):
    return bool(actividad(actividades, lesson_id).get("completada"))


def leccion_intentada(actividades, lesson_id):
    return bool(actividad(actividades, lesson_id).get("intentada"))


def inicio_alguna_leccion(actividades):
    """True si existe cualquier registro de lección: abrirla ya la inicia."""
    return any(actividad(actividades, lesson_id) for lesson_id in (actividades or {}))


def lecciones_de_unidad(lecciones, unidad_id):
    return [lesson for lesson in lecciones if lesson["unidad"] == unidad_id]


def unidad_completada(lecciones, unidad_id, actividades):
    """Una unidad termina cuando todas sus lecciones están completadas."""
    propias = lecciones_de_unidad(lecciones, unidad_id)
    return bool(propias) and all(
        leccion_completada(actividades, lesson["id"]) for lesson in propias
    )


def estado_unidades(unidades, lecciones, actividades):
    """Devuelve el estado de cada unidad, en orden.

    La primera unidad está disponible desde el inicio; cada una de las
    siguientes se desbloquea cuando la anterior tiene todas sus lecciones
    completadas.
    """
    estados = []
    anterior_completa = True
    for unidad in sorted(unidades, key=lambda item: item["numero"]):
        propias = lecciones_de_unidad(lecciones, unidad["id_unidad"])
        completadas = sum(
            leccion_completada(actividades, lesson["id"]) for lesson in propias
        )
        completa = bool(propias) and completadas == len(propias)
        desbloqueada = anterior_completa
        estados.append({
            "id_unidad": unidad["id_unidad"],
            "numero": unidad["numero"],
            "completadas": completadas,
            "total": len(propias),
            "completa": completa,
            "desbloqueada": desbloqueada,
        })
        # Solo cuenta si la unidad estaba disponible: no se salta el orden.
        anterior_completa = completa and desbloqueada
    return estados


def unidad_desbloqueada(unidades, lecciones, unidad_id, actividades):
    return any(
        estado["id_unidad"] == unidad_id and estado["desbloqueada"]
        for estado in estado_unidades(unidades, lecciones, actividades)
    )


def leccion_desbloqueada(unidades, lecciones, lesson, actividades):
    """Una lección es accesible si su unidad está desbloqueada y es la primera
    de la unidad o la anterior ya se completó o se intentó (regla existente
    de la ruta: intentar el quiz permite continuar)."""
    if not unidad_desbloqueada(unidades, lecciones, lesson["unidad"], actividades):
        return False
    propias = lecciones_de_unidad(lecciones, lesson["unidad"])
    indice = next(i for i, item in enumerate(propias) if item["id"] == lesson["id"])
    if indice == 0:
        return True
    previa = propias[indice - 1]["id"]
    return leccion_completada(actividades, previa) or leccion_intentada(actividades, previa)


def siguiente_leccion(unidades, lecciones, lesson, actividades):
    """Primera lección posterior no completada a la que el usuario puede entrar."""
    return next(
        (
            item for item in lecciones
            if item["numero"] > lesson["numero"]
            and not leccion_completada(actividades, item["id"])
            and leccion_desbloqueada(unidades, lecciones, item, actividades)
        ),
        None,
    )
