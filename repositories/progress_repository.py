from database.database import DatabaseConnection


class ProgressRepository:
    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    def find_by_user(self, user_id):
        if not user_id:
            return {}

        connection = self.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT leccion_id, completada, intentada, puntuacion, total
                FROM PROGRESO_LECCION
                WHERE id_persona = ?
                """,
                (user_id,),
            ).fetchall()
            # Cada fila indica que el usuario ya inició esa lección: se crea al
            # abrirla (mark_started) y se actualiza al evaluar su quiz.
            return {
                row["leccion_id"]: {
                    "iniciada": True,
                    "completada": bool(row["completada"]),
                    "intentada": bool(row["intentada"]),
                    "puntuacion": row["puntuacion"],
                    "total": row["total"],
                }
                for row in rows
            }
        finally:
            connection.close()

    def save_activity(self, user_id, lesson_id, activity):
        if not user_id:
            return

        connection = self.database.connect()
        try:
            connection.execute(
                """
                INSERT INTO PROGRESO_LECCION
                    (id_persona, leccion_id, completada, intentada, puntuacion, total)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_persona, leccion_id) DO UPDATE SET
                    completada = excluded.completada,
                    intentada = excluded.intentada,
                    puntuacion = excluded.puntuacion,
                    total = excluded.total
                """,
                (
                    user_id,
                    lesson_id,
                    int(activity.get("completada", False)),
                    int(activity.get("intentada", False)),
                    activity.get("puntuacion", 0),
                    activity.get("total", 0),
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def mark_started(self, user_id, lesson_id):
        """Registra que el usuario abrió una lección, sin alterar su progreso.

        Si la lección ya tiene registro (iniciada, intentada o completada) se
        conserva intacto.
        """
        if not user_id:
            return

        connection = self.database.connect()
        try:
            connection.execute(
                """
                INSERT OR IGNORE INTO PROGRESO_LECCION
                    (id_persona, leccion_id, completada, intentada, puntuacion, total)
                VALUES (?, ?, 0, 0, 0, 0)
                """,
                (user_id, lesson_id),
            )
            connection.commit()
        finally:
            connection.close()

    def save_exercise_attempt(self, user_id, exercise_id, correct):
        """Acumula el resultado de una pregunta del quiz.

        En el esquema actual USUARIO usa id_persona como clave primaria; por eso
        ese mismo identificador se almacena en PROGRESO_EJERCICIO.id_usuario.
        """
        if not user_id or not exercise_id:
            return

        estado = "correcto" if correct else "incorrecto"
        connection = self.database.connect()
        try:
            connection.execute(
                """
                INSERT INTO PROGRESO_EJERCICIO
                    (id_usuario, id_ejercicio, estado, intentos, aciertos, errores)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(id_usuario, id_ejercicio) DO UPDATE SET
                    estado = excluded.estado,
                    intentos = PROGRESO_EJERCICIO.intentos + 1,
                    aciertos = PROGRESO_EJERCICIO.aciertos + excluded.aciertos,
                    errores = PROGRESO_EJERCICIO.errores + excluded.errores
                """,
                (user_id, exercise_id, estado, int(correct), int(not correct)),
            )
            connection.commit()
        finally:
            connection.close()

    def find_exercise_progress(self, user_id):
        if not user_id:
            return {}

        connection = self.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT id_ejercicio, estado, intentos, aciertos, errores
                FROM PROGRESO_EJERCICIO
                WHERE id_usuario = ?
                """,
                (user_id,),
            ).fetchall()
            return {row["id_ejercicio"]: dict(row) for row in rows}
        finally:
            connection.close()

