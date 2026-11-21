from database.database import DatabaseConnection


class UserRepository:
    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    def find_by_email(self, email):
        connection = self.database.connect()
        try:
            row = connection.execute(
                """
                SELECT p.id_persona, p.nombre, p.correo, p.contrasena, u.nivel
                FROM PERSONA p
                LEFT JOIN USUARIO u ON u.id_persona = p.id_persona
                WHERE p.correo = ?
                """,
                (email,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def create(self, nombre, email, password_hash):
        connection = self.database.connect()
        try:
            cursor = connection.execute(
                "INSERT INTO PERSONA (nombre, correo, contrasena) VALUES (?, ?, ?)",
                (nombre, email, password_hash),
            )
            connection.execute(
                "INSERT INTO USUARIO (id_persona) VALUES (?)",
                (cursor.lastrowid,),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def update_password(self, user_id, password_hash):
        connection = self.database.connect()
        try:
            connection.execute(
                "UPDATE PERSONA SET contrasena = ? WHERE id_persona = ?",
                (password_hash, user_id),
            )
            connection.commit()
        finally:
            connection.close()

    def update_level(self, user_id, level):
        connection = self.database.connect()
        try:
            connection.execute(
                "UPDATE USUARIO SET nivel = ? WHERE id_persona = ?",
                (level, user_id),
            )
            connection.commit()
        finally:
            connection.close()
