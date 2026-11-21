import json

from database.database import DatabaseConnection
from services import progreso_service


class RutaModel:
    database = DatabaseConnection()

    @classmethod
    def obtener_unidades(cls):
        connection = cls.database.connect()
        try:
            rows = connection.execute(
                "SELECT id_unidad, numero, nombre, descripcion FROM UNIDAD ORDER BY numero"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    @classmethod
    def obtener_lecciones(cls):
        connection = cls.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT l.id_leccion, l.codigo, l.numero, l.titulo, l.contenido, l.id_unidad,
                       e.id_ejercicio, e.pregunta, e.respuesta_correcta, e.opciones
                FROM LECCION l
                LEFT JOIN EJERCICIO_LECCION e ON e.id_leccion = l.id_leccion
                ORDER BY l.numero, e.numero
                """
            ).fetchall()
            lessons = {}
            for row in rows:
                lesson = lessons.setdefault(row["codigo"], {
                    "id": row["codigo"],
                    "numero": row["numero"],
                    "unidad": row["id_unidad"],
                    "titulo": row["titulo"],
                    "descripcion": row["contenido"],
                    "answers": [],
                    "questions": [],
                    "exercise_ids": [],
                })
                if row["pregunta"] is not None:
                    lesson["answers"].append(row["respuesta_correcta"])
                    lesson["exercise_ids"].append(row["id_ejercicio"])
                    lesson["questions"].append((
                        row["pregunta"],
                        [
                            (option["value"], option["label"])
                            for option in json.loads(row["opciones"])
                        ],
                    ))
            ordered = list(lessons.values())
            # Posición de la lección dentro de su unidad (01-04), para mostrarla.
            positions = {}
            for lesson in ordered:
                positions[lesson["unidad"]] = positions.get(lesson["unidad"], 0) + 1
                lesson["posicion"] = positions[lesson["unidad"]]
            return ordered
        finally:
            connection.close()

    @classmethod
    def obtener_rutas(cls, actividades=None):
        units = cls.obtener_unidades()
        estados = {
            estado["id_unidad"]: estado
            for estado in progreso_service.estado_unidades(
                units, cls.obtener_lecciones(), actividades or {}
            )
        }
        routes = []
        for unit in units:
            estado = estados[unit["id_unidad"]]
            routes.append({
                "id": f"{unit['numero']:02d}",
                "id_unidad": unit["id_unidad"],
                "nombre": unit["nombre"],
                "descripcion": unit["descripcion"],
                "completadas": estado["completadas"],
                "total": estado["total"],
                "progreso": f"{estado['completadas']}/{estado['total']}",
                "completa": estado["completa"],
                "desbloqueada": estado["desbloqueada"],
                "estado": (
                    "Completada" if estado["completa"]
                    else "Continuar" if estado["desbloqueada"]
                    else "Bloqueada"
                ),
            })
        return routes

    @classmethod
    def obtener_ruta(cls, route_id, actividades=None):
        return next(
            (route for route in cls.obtener_rutas(actividades) if route["id"] == route_id),
            None,
        )

    @classmethod
    def obtener_leccion(cls, lesson_id):
        return next(
            (lesson for lesson in cls.obtener_lecciones() if lesson["id"] == lesson_id),
            None,
        )

