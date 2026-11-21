import sqlite3

from database.database import DatabaseConnection


def test_base_limpia_crea_tablas_de_autenticacion(tmp_path):
    database_path = tmp_path / "nivora_limpia.db"
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    DatabaseConnection._initialize_schema(connection)

    tablas = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"PERSONA", "USUARIO", "PROGRESO_LECCION", "EJERCICIO"}.issubset(tablas)

    persona_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(PERSONA)")
    }
    usuario_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(USUARIO)")
    }
    assert {"id_persona", "nombre", "correo", "contrasena"}.issubset(persona_columns)
    assert "id_persona" in usuario_columns
    connection.close()


def test_migra_progreso_de_ejercicio_legacy(tmp_path):
    database_path = tmp_path / "nivora_legacy.db"
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE PROGRESO_EJERCICIO (
            id_progreso_ejercicio INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_ejercicio INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            intentos INTEGER NOT NULL DEFAULT 0
        )"""
    )
    connection.execute(
        "INSERT INTO PROGRESO_EJERCICIO (id_usuario, id_ejercicio, estado, intentos) "
        "VALUES (7, 3, 'incorrecto', 2)"
    )

    DatabaseConnection._initialize_schema(connection)

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(PROGRESO_EJERCICIO)")
    }
    indexes = {
        row["name"]
        for row in connection.execute("PRAGMA index_list(PROGRESO_EJERCICIO)")
    }
    assert {"aciertos", "errores"}.issubset(columns)
    assert "uq_progreso_ejercicio_usuario_ejercicio" in indexes
    row = connection.execute(
        "SELECT intentos, aciertos, errores FROM PROGRESO_EJERCICIO "
        "WHERE id_usuario = 7 AND id_ejercicio = 3"
    ).fetchone()
    assert tuple(row) == (2, 0, 0)  # conserva el registro anterior y añade contadores
    connection.close()
