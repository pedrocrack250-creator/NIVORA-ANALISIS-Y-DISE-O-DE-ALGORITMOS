import json
import os
import sqlite3


class DatabaseConnection:
    def __init__(self, db_type="sqlite", config=None):
        self.db_type = db_type
        self.config = config or {}

    def connect(self):
        if self.db_type != "sqlite":
            raise ValueError("Tipo de base de datos no soportado")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        configured_path = self.config.get("database_path")

        # Cuando hay una aplicación Flask activa, respeta su configuración.
        # Esto permite que las pruebas utilicen una BD temporal sin tocar nivora.db.
        try:
            from flask import current_app, has_app_context
            if has_app_context():
                configured_path = configured_path or current_app.config.get("DATABASE_PATH")
        except ImportError:
            pass

        database = configured_path or os.environ.get(
            "NIVORA_DATABASE_PATH",
            os.path.join(base_dir, "database", "nivora.db"),
        )
        if database != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(database)), exist_ok=True)
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        self._initialize_schema(connection)
        return connection

    @staticmethod
    def _initialize_schema(connection):
        connection.executescript(
            """
            -- Tablas mínimas de autenticación. Antes solo existían en algunas
            -- copias locales de nivora.db, por lo que un clon limpio no podía registrar usuarios.
            CREATE TABLE IF NOT EXISTS PERSONA (
                id_persona INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS USUARIO (
                id_persona INTEGER PRIMARY KEY,
                FOREIGN KEY (id_persona) REFERENCES PERSONA(id_persona) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS PROGRESO_LECCION (
                id_persona INTEGER NOT NULL,
                leccion_id TEXT NOT NULL,
                completada INTEGER NOT NULL DEFAULT 0,
                intentada INTEGER NOT NULL DEFAULT 0,
                puntuacion INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (id_persona, leccion_id)
            );
            CREATE TABLE IF NOT EXISTS PROGRESO_EJERCICIO (
                id_progreso_ejercicio INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_ejercicio INTEGER NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                intentos INTEGER NOT NULL DEFAULT 0,
                aciertos INTEGER NOT NULL DEFAULT 0,
                errores INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS UNIDAD (
                id_unidad INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                numero INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS LECCION (
                id_leccion INTEGER PRIMARY KEY,
                titulo TEXT NOT NULL,
                contenido TEXT NOT NULL,
                numero INTEGER NOT NULL,
                id_unidad INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS EJERCICIO (
                id_ejercicio INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                dificultad TEXT NOT NULL,
                codigo_inicial TEXT,
                solucion_esperada TEXT,
                id_unidad INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS EJERCICIO_LECCION (
                id_ejercicio INTEGER PRIMARY KEY,
                id_leccion INTEGER NOT NULL,
                numero INTEGER NOT NULL,
                pregunta TEXT NOT NULL,
                respuesta_correcta TEXT NOT NULL,
                opciones TEXT NOT NULL
            );
            """
        )
        # Migración compatible con la tabla PROGRESO_EJERCICIO que ya existía
        # en algunas copias de Nivora con solo estado e intentos.
        progress_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(PROGRESO_EJERCICIO)").fetchall()
        }
        if "aciertos" not in progress_columns:
            connection.execute(
                "ALTER TABLE PROGRESO_EJERCICIO ADD COLUMN aciertos INTEGER NOT NULL DEFAULT 0"
            )
        if "errores" not in progress_columns:
            connection.execute(
                "ALTER TABLE PROGRESO_EJERCICIO ADD COLUMN errores INTEGER NOT NULL DEFAULT 0"
            )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_progreso_ejercicio_usuario_ejercicio "
            "ON PROGRESO_EJERCICIO (id_usuario, id_ejercicio)"
        )

        # Nivel inicial elegido en /nivel: permite volver a mostrar la
        # recomendación tras cerrar sesión mientras no se haya iniciado ninguna lección.
        user_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(USUARIO)").fetchall()
        }
        if "nivel" not in user_columns:
            connection.execute("ALTER TABLE USUARIO ADD COLUMN nivel TEXT")

        lesson_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(LECCION)").fetchall()
        }
        if "codigo" not in lesson_columns:
            connection.execute("ALTER TABLE LECCION ADD COLUMN codigo TEXT")

        units = [
            (1, "Fundamentos de Python", "Aprende variables, tipos de datos, operadores y entrada y salida de datos.", 1),
            (2, "Control de flujo", "Aprende a utilizar condicionales y ciclos para controlar tus programas.", 2),
            (3, "Listas y estructuras", "Aprende a trabajar con listas y otras estructuras para organizar información.", 3),
            (4, "Funciones", "Crea funciones para organizar y reutilizar tu código.", 4),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO UNIDAD (id_unidad, nombre, descripcion, numero) VALUES (?, ?, ?, ?)",
            units,
        )

        lessons = [
            (1, "Variables y tipos de datos", "Guarda información y reconoce los tipos básicos de Python.", 1, 1, "variables"),
            (2, "Operadores y expresiones", "Realiza operaciones y compara valores.", 2, 1, "operadores"),
            (3, "Entrada y salida de datos", "Muestra información y recibe datos del usuario.", 3, 1, "entrada_salida"),
            (4, "Repaso de fundamentos", "Comprueba lo aprendido en la primera ruta.", 4, 1, "repaso_fundamentos"),
            # Unidad 02 · Control de flujo
            (5, "Condicionales if y else", "Toma decisiones según una condición.", 5, 2, "condicionales"),
            (6, "Varias condiciones con elif", "Evalúa varios casos en orden y combina condiciones.", 6, 2, "elif"),
            (7, "Ciclo for", "Repite instrucciones para cada elemento de una secuencia.", 7, 2, "ciclo_for"),
            (8, "Ciclo while", "Repite instrucciones mientras una condición sea verdadera.", 8, 2, "ciclo_while"),
            # Unidad 03 · Listas y estructuras
            (9, "Listas e índices", "Crea listas y accede a sus elementos por posición.", 9, 3, "listas"),
            (10, "Métodos de listas", "Agrega, elimina y ordena elementos de una lista.", 10, 3, "metodos_listas"),
            (11, "Tuplas", "Agrupa valores que no deben cambiar.", 11, 3, "tuplas"),
            (12, "Diccionarios", "Guarda información en pares clave-valor.", 12, 3, "diccionarios"),
            # Unidad 04 · Funciones
            (13, "Definir funciones", "Agrupa instrucciones bajo un nombre para reutilizarlas.", 13, 4, "definir_funciones"),
            (14, "Parámetros y argumentos", "Envía información a una función.", 14, 4, "parametros"),
            (15, "Valores de retorno", "Devuelve resultados para usarlos después.", 15, 4, "retorno"),
            (16, "Repaso de funciones", "Comprueba lo aprendido en la unidad de funciones.", 16, 4, "repaso_funciones"),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO LECCION (id_leccion, titulo, contenido, numero, id_unidad, codigo) VALUES (?, ?, ?, ?, ?, ?)",
            lessons,
        )

        exercises = [
            (1, "Pregunta 1", "¿Qué nombre tiene el valor en nombre = \"Ana\"?", "nombre"),
            (2, "Pregunta 2", "¿Qué tipo de dato es 20?", "int"),
            (3, "Pregunta 3", "¿Cuál representa verdadero o falso?", "True"),
            (4, "Pregunta 1", "¿Cuál es el resultado de 3 + 4?", "7"),
            (5, "Pregunta 2", "¿Qué devuelve 5 > 2?", "True"),
            (6, "Pregunta 3", "¿Qué operador compara igualdad?", "=="),
            (7, "Pregunta 1", "¿Qué función muestra texto?", "print"),
            (8, "Pregunta 2", "¿Qué función recibe datos?", "input"),
            (9, "Pregunta 3", "¿Qué devuelve input normalmente?", "texto"),
            (10, "Pregunta 1", "¿Qué estructura guarda varios valores ordenados?", "lista"),
            (11, "Pregunta 2", "¿Qué función obtiene la cantidad de elementos?", "len"),
            (12, "Pregunta 3", "¿Qué método agrega un elemento a una lista?", "append"),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO (id_ejercicio, titulo, descripcion, dificultad, solucion_esperada, id_unidad) VALUES (?, ?, ?, 'basico', ?, 1)",
            [(number, title, question, answer) for number, title, question, answer in exercises],
        )

        # Preguntas de los quizzes de las unidades 2-4. Usan identificadores a
        # partir de 25 porque 13-24 pertenecen a los ejercicios de práctica.
        # (id_ejercicio, id_leccion, número, pregunta, respuesta, opciones, id_unidad)
        unit_questions = [
            (25, 5, 1, "¿Qué palabra inicia una condición en Python?", "if", [("for", "for"), ("if", "if")], 2),
            (26, 5, 2, "¿Qué bloque se ejecuta cuando la condición es falsa?", "else", [("else", "else"), ("print", "print")], 2),
            (27, 5, 3, "¿Qué se muestra con: if 3 > 5: print(\"A\") else: print(\"B\")?", "B", [("A", "A"), ("B", "B")], 2),
            (28, 6, 1, "¿Qué palabra evalúa otra condición si la anterior fue falsa?", "elif", [("elif", "elif"), ("then", "then")], 2),
            (29, 6, 2, "En un bloque if / elif / else, ¿cuántos bloques se ejecutan como máximo?", "uno", [("todos", "Todos los que se cumplan"), ("uno", "Solo uno")], 2),
            (30, 6, 3, "¿Qué operador exige que se cumplan dos condiciones a la vez?", "and", [("and", "and"), ("or", "or")], 2),
            (31, 7, 1, "¿Qué números genera range(3)?", "0, 1, 2", [("1, 2, 3", "1, 2, 3"), ("0, 1, 2", "0, 1, 2")], 2),
            (32, 7, 2, "¿Cuántas veces se repite: for i in range(5)?", "5", [("5", "5"), ("4", "4")], 2),
            (33, 7, 3, "¿Qué ciclo recorre cada elemento de una lista?", "for", [("if", "if"), ("for", "for")], 2),
            (34, 8, 1, "¿Cuándo se detiene un ciclo while?", "falsa", [("falsa", "Cuando su condición es falsa"), ("una_vuelta", "Después de una vuelta")], 2),
            (35, 8, 2, "¿Qué instrucción termina un ciclo inmediatamente?", "break", [("continue", "continue"), ("break", "break")], 2),
            (36, 8, 3, "¿Qué instrucción salta a la siguiente vuelta del ciclo?", "continue", [("continue", "continue"), ("break", "break")], 2),
            (37, 9, 1, "¿Qué índice tiene el primer elemento de una lista?", "0", [("1", "1"), ("0", "0")], 3),
            (38, 9, 2, "¿Qué devuelve [10, 20, 30][1]?", "20", [("20", "20"), ("10", "10")], 3),
            (39, 9, 3, "¿Qué devuelve [5, 6, 7][-1]?", "7", [("5", "5"), ("7", "7")], 3),
            (40, 10, 1, "¿Qué método elimina y devuelve el último elemento?", "pop", [("pop", "pop"), ("append", "append")], 3),
            (41, 10, 2, "¿Qué método ordena una lista?", "sort", [("len", "len"), ("sort", "sort")], 3),
            (42, 10, 3, "¿Qué método elimina la primera aparición de un valor?", "remove", [("remove", "remove"), ("insert", "insert")], 3),
            (43, 11, 1, "¿Con qué símbolos se crea una tupla?", "()", [("[]", "[ ]"), ("()", "( )")], 3),
            (44, 11, 2, "¿Se puede cambiar un elemento de una tupla después de crearla?", "no", [("no", "No"), ("si", "Sí")], 3),
            (45, 11, 3, "¿Qué devuelve (4, 8)[0]?", "4", [("8", "8"), ("4", "4")], 3),
            (46, 12, 1, "¿Con qué símbolos se crea un diccionario?", "{}", [("{}", "{ }"), ("()", "( )")], 3),
            (47, 12, 2, "¿Qué devuelve {\"edad\": 20}[\"edad\"]?", "20", [("edad", "edad"), ("20", "20")], 3),
            (48, 12, 3, "¿Qué método devuelve las claves de un diccionario?", "keys", [("keys", "keys"), ("values", "values")], 3),
            (49, 13, 1, "¿Qué palabra se usa para definir una función?", "def", [("function", "function"), ("def", "def")], 4),
            (50, 13, 2, "¿Cómo se ejecuta la función saludar?", "saludar()", [("saludar()", "saludar()"), ("saludar", "saludar")], 4),
            (51, 13, 3, "¿Con qué símbolo termina la línea que empieza con def?", ":", [(";", ";"), (":", ":")], 4),
            (52, 14, 1, "En def sumar(a, b), ¿qué son a y b?", "parametros", [("parametros", "Parámetros"), ("globales", "Variables globales")], 4),
            (53, 14, 2, "Con def saludar(saludo=\"Hola\"), ¿qué valor tiene saludo al llamar saludar()?", "Hola", [("None", "None"), ("Hola", "Hola")], 4),
            (54, 14, 3, "¿Cuántos argumentos recibe la llamada sumar(2, 3)?", "2", [("2", "2"), ("1", "1")], 4),
            (55, 15, 1, "¿Qué palabra devuelve un valor desde una función?", "return", [("print", "print"), ("return", "return")], 4),
            (56, 15, 2, "¿Qué devuelve una función que no tiene return?", "None", [("None", "None"), ("0", "0")], 4),
            (57, 15, 3, "Con def doble(n): return n * 2, ¿cuánto vale doble(4)?", "8", [("8", "8"), ("4", "4")], 4),
            (58, 16, 1, "¿Una variable creada dentro de una función existe fuera de ella?", "no", [("si", "Sí"), ("no", "No")], 4),
            (59, 16, 2, "¿Cómo se llama una función que se llama a sí misma?", "recursiva", [("recursiva", "Recursiva"), ("anonima", "Anónima")], 4),
            (60, 16, 3, "¿Qué devuelve len(\"hola\")?", "4", [("5", "5"), ("4", "4")], 4),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO (id_ejercicio, titulo, descripcion, dificultad, solucion_esperada, id_unidad) VALUES (?, ?, ?, 'basico', ?, ?)",
            [
                (exercise_id, f"Pregunta {number}", question, answer, unit_id)
                for exercise_id, _lesson, number, question, answer, _options, unit_id in unit_questions
            ],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO_LECCION (id_ejercicio, id_leccion, numero, pregunta, respuesta_correcta, opciones) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    exercise_id, lesson_id, number, question, answer,
                    json.dumps(
                        [{"value": value, "label": label} for value, label in option_list],
                        ensure_ascii=False,
                    ),
                )
                for exercise_id, lesson_id, number, question, answer, option_list, _unit in unit_questions
            ],
        )

        practice_exercises = [
            (13, "Saludo personalizado", "Pide un nombre con input() y muestra un saludo con print().", "basico", 1, "print(f'Hola, {nombre}')"),
            (14, "Promedio de una lista", "Calcula el promedio de una lista de números sin usar bibliotecas.", "intermedio", 3, "sum(numeros) / len(numeros)"),
            (15, "Números pares", "Imprime los números pares del 1 al 20 usando un ciclo.", "basico", 2, "for n in range(2, 21, 2): print(n)"),
            (16, "Factorial recursivo", "Escribe una función recursiva que calcule el factorial de n.", "avanzado", 4, "def factorial(n): return 1 if n <= 1 else n * factorial(n - 1)"),
            (17, "Contar vocales", "Cuenta cuántas vocales tiene un texto.", "intermedio", 2, "sum(1 for c in texto.lower() if c in 'aeiou')"),
            (18, "Invertir una lista", "Devuelve una lista con los elementos en orden inverso sin usar reverse().", "intermedio", 3, "lista[::-1]"),
            (19, "Función con valores por defecto", "Crea una función saludar(nombre, saludo='Hola') que devuelva el mensaje.", "intermedio", 4, "def saludar(nombre, saludo='Hola'): return f'{saludo}, {nombre}'"),
            (20, "Tabla de multiplicar", "Muestra la tabla de multiplicar de un número del 1 al 10.", "basico", 2, "for i in range(1, 11): print(n * i)"),
            (21, "Máximo sin max()", "Encuentra el mayor elemento de una lista recorriéndola con un ciclo.", "avanzado", 3, "mayor = lista[0]; for x in lista: mayor = x if x > mayor else mayor"),
            (22, "Palíndromo", "Comprueba si una palabra se lee igual al derecho y al revés.", "avanzado", 2, "palabra == palabra[::-1]"),
            (23, "Área de un rectángulo", "Escribe una función area(base, altura) que devuelva el área.", "basico", 4, "def area(base, altura): return base * altura"),
            (24, "Filtrar con comprensión", "Crea una lista con los cuadrados de los números impares de otra lista.", "avanzado", 3, "[n * n for n in lista if n % 2 == 1]"),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO (id_ejercicio, titulo, descripcion, dificultad, id_unidad, solucion_esperada) VALUES (?, ?, ?, ?, ?, ?)",
            practice_exercises,
        )

        options = [
            (1, 1, 1, "nombre", '[{"value": "nombre", "label": "nombre"}, {"value": "Ana", "label": "Ana"}]'),
            (2, 1, 2, "int", '[{"value": "int", "label": "int"}, {"value": "str", "label": "str"}]'),
            (3, 1, 3, "True", '[{"value": "True", "label": "True"}, {"value": "10", "label": "10"}]'),
            (4, 2, 1, "7", '[{"value": "7", "label": "7"}, {"value": "12", "label": "12"}]'),
            (5, 2, 2, "True", '[{"value": "True", "label": "True"}, {"value": "False", "label": "False"}]'),
            (6, 2, 3, "==", '[{"value": "==", "label": "=="}, {"value": "=", "label": "="}]'),
            (7, 3, 1, "print", '[{"value": "print", "label": "print"}, {"value": "input", "label": "input"}]'),
            (8, 3, 2, "input", '[{"value": "input", "label": "input"}, {"value": "print", "label": "print"}]'),
            (9, 3, 3, "texto", '[{"value": "texto", "label": "texto"}, {"value": "int", "label": "int"}]'),
            (10, 4, 1, "lista", '[{"value": "lista", "label": "lista"}, {"value": "if", "label": "if"}]'),
            (11, 4, 2, "len", '[{"value": "len", "label": "len"}, {"value": "sum", "label": "sum"}]'),
            (12, 4, 3, "append", '[{"value": "append", "label": "append"}, {"value": "add", "label": "add"}]'),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO_LECCION (id_ejercicio, id_leccion, numero, pregunta, respuesta_correcta, opciones) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    exercise_id,
                    lesson_id,
                    number,
                    next(item[2] for item in exercises if item[0] == exercise_id),
                    correct_answer,
                    option_data,
                )
                for exercise_id, lesson_id, number, correct_answer, option_data in options
            ],
        )
        connection.commit()
