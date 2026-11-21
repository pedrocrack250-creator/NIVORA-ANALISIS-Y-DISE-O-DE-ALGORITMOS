from database.database import DatabaseConnection


class ExerciseRepository:
    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    def find_all(self):
        """Devuelve todos los ejercicios con el nombre de su unidad."""
        connection = self.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT e.id_ejercicio, e.titulo, e.descripcion, e.dificultad,
                       e.id_unidad, u.nombre AS unidad
                FROM EJERCICIO e
                JOIN UNIDAD u ON u.id_unidad = e.id_unidad
                ORDER BY e.id_ejercicio
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def find_quiz_questions(self, user_id, progress_repository):
        """Obtiene preguntas del quiz junto con el progreso real del usuario."""
        connection = self.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT e.id_ejercicio, e.titulo, e.dificultad,
                       el.numero, el.pregunta, l.codigo AS lesson_id,
                       l.titulo AS lesson_title
                FROM EJERCICIO e
                JOIN EJERCICIO_LECCION el ON el.id_ejercicio = e.id_ejercicio
                JOIN LECCION l ON l.id_leccion = el.id_leccion
                ORDER BY l.numero, el.numero
                """
            ).fetchall()
            progress = progress_repository.find_exercise_progress(user_id)
            questions = []
            for row in rows:
                item = dict(row)
                activity = progress.get(item["id_ejercicio"], {})
                item.update({
                    "estado": activity.get("estado", "pendiente"),
                    "intentos": activity.get("intentos", 0),
                    "aciertos": activity.get("aciertos", 0),
                    "errores": activity.get("errores", 0),
                })
                questions.append(item)
            return questions
        finally:
            connection.close()
