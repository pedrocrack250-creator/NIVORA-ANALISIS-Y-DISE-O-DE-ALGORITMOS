"""Reglas de progreso y desbloqueo de la ruta de aprendizaje.

Única fuente de verdad para decidir cuándo una lección está completada,
cuándo una unidad está terminada y qué unidades o lecciones están
desbloqueadas. Trabaja con los registros del usuario (`PROGRESO_LECCION`,
cargados en la sesión al iniciar sesión y actualizados en cada quiz), por lo
que no depende de contadores mostrados en pantalla.

El orden de las unidades y de las lecciones por repasar se calcula con el
Merge Sort propio de ``services.algoritmos.merge_sort`` (no con ``sorted()``).
"""
from services.algoritmos.merge_sort import merge_sort


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
    # Merge Sort (estable, O(n log n)): el orden de las unidades define el desbloqueo.
    for unidad in merge_sort(unidades, clave=lambda item: item["numero"]).elementos:
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


def lecciones_para_repasar(lecciones, actividades):
    """Lecciones intentadas que aún no se completan, de menor a mayor acierto.

    Se ordenan con Merge Sort por (proporción de aciertos, posición en la ruta):
    arriba queda la lección en la que el estudiante más necesita repasar. Al ser
    estable, a igual acierto se conserva el orden de la ruta.
    """
    pendientes = []
    for lesson in lecciones:
        registro = actividad(actividades, lesson["id"])
        if not registro.get("intentada") or registro.get("completada"):
            continue
        total = registro.get("total") or 0
        puntuacion = registro.get("puntuacion") or 0
        acierto = puntuacion / total if total else 0.0
        pendientes.append({
            "id": lesson["id"],
            "titulo": lesson["titulo"],
            "unidad": lesson["unidad"],
            "numero": lesson["numero"],
            "puntuacion": puntuacion,
            "total": total,
            "porcentaje": round(acierto * 100),
            "acierto": acierto,
        })
    return merge_sort(pendientes, clave=lambda item: (item["acierto"], item["numero"])).elementos


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
