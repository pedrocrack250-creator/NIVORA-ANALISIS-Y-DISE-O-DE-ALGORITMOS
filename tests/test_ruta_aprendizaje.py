"""Recomendación inicial, desbloqueo de unidades y laboratorio integrado en Aprender.

Cada prueba crea su propia aplicación con TestingConfig, que asigna una base
SQLite temporal: nunca se usa ni se modifica database/nivora.db.
"""
import json
import re
import sqlite3

import pytest

from app import create_app
from config import TestingConfig
from database.database import DatabaseConnection
from services import progreso_service
from services.algoritmos import catalogo

CORREO = "ana@example.com"
CLAVE = "password-123"


# --- Utilidades ---------------------------------------------------------------

@pytest.fixture
def app():
    return create_app(TestingConfig)


@pytest.fixture
def cliente(app):
    return app.test_client()


def csrf(cliente):
    with cliente.session_transaction() as sesion:
        token = sesion.get("csrf_token")
    if token is None:  # el login y el registro reinician la sesión
        cliente.get("/login")
        with cliente.session_transaction() as sesion:
            token = sesion["csrf_token"]
    return token


def registrar(cliente, nivel="no_se_nada"):
    cliente.get("/registro")
    respuesta = cliente.post("/registro", data={
        "csrf_token": csrf(cliente), "nombre": "Ana", "email": CORREO, "password": CLAVE,
    })
    assert respuesta.status_code == 302 and respuesta.headers["Location"].endswith("/nivel")
    respuesta = cliente.post("/nivel", data={"csrf_token": csrf(cliente), "nivel_inicial": nivel})
    assert respuesta.status_code == 302


def cerrar_sesion(cliente):
    cliente.get("/logout")
    with cliente.session_transaction() as sesion:
        assert "usuario" not in sesion


def iniciar_sesion(cliente):
    cliente.get("/login")
    respuesta = cliente.post("/login", data={
        "csrf_token": csrf(cliente), "email": CORREO, "password": CLAVE,
    })
    assert respuesta.status_code == 302


def responder(cliente, leccion, respuestas):
    datos = {"csrf_token": csrf(cliente)}
    datos.update({f"respuesta_{i}": v for i, v in enumerate(respuestas, start=1)})
    return cliente.post(f"/aprender/leccion/{leccion}/completar", data=datos)


def completar_unidad(cliente, respuestas):
    for leccion, valores in respuestas.items():
        assert cliente.get(f"/aprender/leccion/{leccion}").status_code == 200
        assert responder(cliente, leccion, valores).status_code == 200


def estado_unidades(cliente):
    """Devuelve {'01': 'abierta'|'bloqueada', ...} leyendo la página Aprender."""
    html = cliente.get("/aprender").get_data(as_text=True)
    estados = {}
    for numero in ("01", "02", "03", "04"):
        abierta = f'href="/aprender/ruta/{numero}"' in html
        estados[numero] = "abierta" if abierta else "bloqueada"
    return estados


def filas_progreso(app, correo=CORREO):
    with app.app_context():
        conexion = DatabaseConnection().connect()
        try:
            return {
                fila["leccion_id"]: dict(fila)
                for fila in conexion.execute(
                    "SELECT pl.* FROM PROGRESO_LECCION pl JOIN PERSONA p "
                    "ON p.id_persona = pl.id_persona WHERE p.correo = ?", (correo,)
                )
            }
        finally:
            conexion.close()


MARCA_RECOMENDACION = "data-recomendacion-inicial"


# --- 1-3. Mensaje de recomendación inicial ----------------------------------

def test_usuario_nuevo_ve_la_recomendacion_inicial(cliente):
    registrar(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert MARCA_RECOMENDACION in html
    assert "Te recomendamos empezar desde cero" in html


def test_al_iniciar_una_leccion_el_mensaje_desaparece_sin_completarla(app, cliente):
    registrar(cliente)
    assert cliente.get("/aprender/leccion/variables").status_code == 200

    # Solo se abrió: no se ha intentado ni completado, pero ya cuenta como iniciada.
    fila = filas_progreso(app)["variables"]
    assert (fila["completada"], fila["intentada"]) == (0, 0)
    assert MARCA_RECOMENDACION not in cliente.get("/aprender").get_data(as_text=True)
    # Volver de nuevo a Aprender: sigue oculto.
    assert MARCA_RECOMENDACION not in cliente.get("/aprender").get_data(as_text=True)


def test_el_mensaje_sigue_oculto_tras_cerrar_sesion_y_volver(cliente):
    registrar(cliente)
    cliente.get("/aprender/leccion/variables")
    cerrar_sesion(cliente)
    iniciar_sesion(cliente)
    assert MARCA_RECOMENDACION not in cliente.get("/aprender").get_data(as_text=True)


def test_sin_iniciar_lecciones_la_recomendacion_se_conserva_al_volver(cliente):
    registrar(cliente)
    cerrar_sesion(cliente)
    iniciar_sesion(cliente)
    assert MARCA_RECOMENDACION in cliente.get("/aprender").get_data(as_text=True)


def test_la_ruta_historica_de_variables_tambien_inicia_la_leccion(app, cliente):
    registrar(cliente)
    cliente.get("/aprender/ruta/01")  # ver la unidad no inicia ninguna lección
    assert MARCA_RECOMENDACION in cliente.get("/aprender").get_data(as_text=True)
    cliente.get("/aprender/leccion/variables")
    assert "variables" in filas_progreso(app)


def test_abrir_una_leccion_no_altera_un_progreso_existente(app, cliente, respuestas_correctas):
    registrar(cliente)
    responder(cliente, "variables", respuestas_correctas["01"]["variables"])
    cliente.get("/aprender/leccion/variables")
    assert filas_progreso(app)["variables"]["completada"] == 1


# --- 4-7. Desbloqueo progresivo de unidades ----------------------------------

def test_solo_la_unidad_01_esta_disponible_al_inicio(cliente):
    registrar(cliente)
    assert estado_unidades(cliente) == {
        "01": "abierta", "02": "bloqueada", "03": "bloqueada", "04": "bloqueada",
    }


def test_las_unidades_se_desbloquean_en_orden_y_se_conservan(app, cliente, respuestas_correctas):
    registrar(cliente)

    completar_unidad(cliente, respuestas_correctas["01"])
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "4/4" in html
    assert estado_unidades(cliente) == {
        "01": "abierta", "02": "abierta", "03": "bloqueada", "04": "bloqueada",
    }

    completar_unidad(cliente, respuestas_correctas["02"])
    assert estado_unidades(cliente)["03"] == "abierta"
    assert estado_unidades(cliente)["04"] == "bloqueada"

    completar_unidad(cliente, respuestas_correctas["03"])
    assert estado_unidades(cliente)["04"] == "abierta"

    # 7. Cerrar sesión y volver: el estado se reconstruye desde la base de datos.
    cerrar_sesion(cliente)
    iniciar_sesion(cliente)
    assert estado_unidades(cliente) == {
        "01": "abierta", "02": "abierta", "03": "abierta", "04": "abierta",
    }
    html = cliente.get("/aprender").get_data(as_text=True)
    assert html.count("4/4") == 3 and "0/4" in html
    progreso = cliente.get("/progreso").get_data(as_text=True)
    assert progreso.count("width: 100%;") == 3  # tres barras de unidad llenas
    assert len(filas_progreso(app)) == 12


def test_unidad_no_se_desbloquea_con_una_leccion_solo_intentada(cliente, respuestas_correctas):
    registrar(cliente)
    lecciones = list(respuestas_correctas["01"].items())
    for leccion, valores in lecciones[:3]:
        responder(cliente, leccion, valores)
    responder(cliente, "repaso_fundamentos", ["if", "sum", "add"])  # quiz fallado
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "3/4" in html
    assert estado_unidades(cliente)["02"] == "bloqueada"


def test_no_se_accede_a_lecciones_ni_unidades_bloqueadas(app, cliente, respuestas_correctas):
    registrar(cliente)
    respuesta = cliente.get("/aprender/ruta/02")
    assert respuesta.status_code == 302 and respuesta.headers["Location"].endswith("/aprender")
    respuesta = cliente.get("/aprender/leccion/condicionales")
    assert respuesta.status_code == 302
    # Tampoco se puede completar por POST directo.
    respuesta = responder(cliente, "condicionales", respuestas_correctas["02"]["condicionales"])
    assert respuesta.status_code == 302
    assert "condicionales" not in filas_progreso(app)
    # Dentro de una unidad abierta se respeta el orden de lecciones.
    respuesta = cliente.get("/aprender/leccion/operadores")
    assert respuesta.status_code == 302 and respuesta.headers["Location"].endswith("/aprender/ruta/01")


def test_ruta_de_la_unidad_02_muestra_sus_lecciones(cliente, respuestas_correctas):
    registrar(cliente)
    completar_unidad(cliente, respuestas_correctas["01"])
    html = cliente.get("/aprender/ruta/02").get_data(as_text=True)
    assert "Control de flujo" in html
    assert "/aprender/leccion/condicionales" in html
    assert "Ciclo while" in html
    assert "Variables y tipos de datos" not in html
    leccion = cliente.get("/aprender/leccion/condicionales").get_data(as_text=True)
    assert "Unidad 02 · Lección 01 · Control de flujo" in leccion


def test_al_terminar_una_unidad_la_siguiente_leccion_es_la_de_la_nueva_unidad(cliente, respuestas_correctas):
    registrar(cliente)
    lecciones = list(respuestas_correctas["01"].items())
    for leccion, valores in lecciones[:3]:
        responder(cliente, leccion, valores)
    # Fallar la última lección no debe enviar a una unidad bloqueada.
    fallo = responder(cliente, "repaso_fundamentos", ["if", "sum", "add"]).get_data(as_text=True)
    assert "/aprender/leccion/condicionales" not in fallo
    assert "/aprender/ruta/01" in fallo
    exito = responder(cliente, "repaso_fundamentos", lecciones[3][1]).get_data(as_text=True)
    assert "/aprender/leccion/condicionales" in exito


# --- Reglas del servicio de progreso (sin base de datos) ----------------------

UNIDADES = [{"id_unidad": n, "numero": n} for n in (1, 2, 3, 4)]
LECCIONES = [
    {"id": f"u{u}l{l}", "unidad": u, "numero": (u - 1) * 4 + l}
    for u in (1, 2, 3, 4) for l in (1, 2, 3, 4)
]


def completas(*unidades):
    return {
        leccion["id"]: {"completada": True, "intentada": True}
        for leccion in LECCIONES if leccion["unidad"] in unidades
    }


def test_servicio_desbloquea_cada_unidad_al_completar_la_anterior():
    def abiertas(actividades):
        return [e["desbloqueada"] for e in progreso_service.estado_unidades(UNIDADES, LECCIONES, actividades)]

    assert abiertas({}) == [True, False, False, False]
    assert abiertas(completas(1)) == [True, True, False, False]
    assert abiertas(completas(1, 2)) == [True, True, True, False]
    assert abiertas(completas(1, 2, 3)) == [True, True, True, True]
    # Completar una unidad posterior sin la anterior no salta el orden.
    assert abiertas(completas(2)) == [True, False, False, False]


def test_servicio_detecta_si_se_inicio_alguna_leccion():
    assert progreso_service.inicio_alguna_leccion({}) is False
    assert progreso_service.inicio_alguna_leccion(
        {"u1l1": {"iniciada": True, "completada": False, "intentada": False}}
    ) is True


def test_servicio_acepta_registros_heredados_booleanos():
    actividades = {leccion["id"]: True for leccion in LECCIONES if leccion["unidad"] == 1}
    assert progreso_service.unidad_completada(LECCIONES, 1, actividades)


# --- Datos de las unidades -----------------------------------------------------

def test_cada_unidad_tiene_cuatro_lecciones_con_quiz_valido(tmp_path):
    conexion = sqlite3.connect(tmp_path / "limpia.db")
    conexion.row_factory = sqlite3.Row
    DatabaseConnection._initialize_schema(conexion)
    DatabaseConnection._initialize_schema(conexion)  # idempotente: sin duplicados

    por_unidad = {
        fila[0]: fila[1]
        for fila in conexion.execute("SELECT id_unidad, COUNT(*) FROM LECCION GROUP BY id_unidad")
    }
    assert por_unidad == {1: 4, 2: 4, 3: 4, 4: 4}
    assert conexion.execute("SELECT COUNT(*) FROM UNIDAD").fetchone()[0] == 4
    # Las lecciones originales conservan identificador, código y unidad.
    originales = conexion.execute(
        "SELECT id_leccion, codigo, id_unidad FROM LECCION WHERE id_leccion <= 4 ORDER BY id_leccion"
    ).fetchall()
    assert [tuple(f) for f in originales] == [
        (1, "variables", 1), (2, "operadores", 1), (3, "entrada_salida", 1), (4, "repaso_fundamentos", 1),
    ]
    for fila in conexion.execute(
        "SELECT el.id_leccion, el.respuesta_correcta, el.opciones FROM EJERCICIO_LECCION el"
    ):
        assert fila["respuesta_correcta"] in {op["value"] for op in json.loads(fila["opciones"])}
    preguntas = dict(conexion.execute(
        "SELECT id_leccion, COUNT(*) FROM EJERCICIO_LECCION GROUP BY id_leccion"
    ).fetchall())
    assert set(preguntas.values()) == {3} and len(preguntas) == 16
    conexion.close()


def test_respuestas_de_prueba_coinciden_con_la_base(app, respuestas_correctas):
    from models.ruta_model import RutaModel
    with app.app_context():
        lecciones = {leccion["id"]: leccion for leccion in RutaModel.obtener_lecciones()}
    for unidad in respuestas_correctas.values():
        for leccion, respuestas in unidad.items():
            assert lecciones[leccion]["answers"] == respuestas


def test_migracion_agrega_nivel_a_usuario_existente(tmp_path):
    conexion = sqlite3.connect(tmp_path / "legacy.db")
    conexion.row_factory = sqlite3.Row
    conexion.execute("CREATE TABLE USUARIO (id_persona INTEGER PRIMARY KEY)")
    conexion.execute("INSERT INTO USUARIO (id_persona) VALUES (5)")
    DatabaseConnection._initialize_schema(conexion)
    columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(USUARIO)")}
    assert "nivel" in columnas
    assert conexion.execute("SELECT id_persona FROM USUARIO").fetchone()[0] == 5
    conexion.close()


# --- 8-11. Laboratorio integrado en Aprender y navegación ---------------------

def enlaces(html):
    return re.findall(r'href="(/[^"#]*)', html)


def seccion_laboratorio(html):
    inicio = html.index('id="laboratorio"')
    return html[inicio:html.index("</section>", inicio)]


def test_practicar_desaparece_del_menu(cliente):
    for autenticado in (False, True):
        if autenticado:
            registrar(cliente)
        html = cliente.get("/").get_data(as_text=True)
        cabecera = html[html.index("<header>"):html.index("</header>")]
        assert "Practicar" not in cabecera
        assert "/practica" not in html
        assert 'href="/aprender"' in cabecera


def test_aprender_muestra_las_unidades_y_despues_el_laboratorio(cliente):
    registrar(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert html.index("Funciones") < html.index('id="laboratorio"')
    laboratorio = seccion_laboratorio(html)
    for nombre in ("Merge Sort", "Programación dinámica", "Backtracking", "Algoritmo voraz",
                   "Kruskal", "Prim", "Union-Find"):
        assert nombre in laboratorio
    assert len(enlaces(laboratorio)) == len(catalogo.INTERACTIVOS) + len(catalogo.EDUCATIVOS) == 7


def test_todos_los_laboratorios_funcionan_desde_aprender(cliente):
    registrar(cliente)
    laboratorio = seccion_laboratorio(cliente.get("/aprender").get_data(as_text=True))
    for url in enlaces(laboratorio):
        respuesta = cliente.get(url)
        assert respuesta.status_code == 200, url
        assert "Volver al laboratorio" in respuesta.get_data(as_text=True), url


def test_los_laboratorios_no_alteran_el_progreso_de_las_unidades(app, cliente):
    registrar(cliente)
    laboratorio = seccion_laboratorio(cliente.get("/aprender").get_data(as_text=True))
    for url in enlaces(laboratorio):
        cliente.get(url)
    assert filas_progreso(app) == {}
    assert MARCA_RECOMENDACION in cliente.get("/aprender").get_data(as_text=True)


@pytest.mark.parametrize("antigua, nueva", [
    ("/practica", "/aprender#laboratorio"),
    ("/practica/laboratorio", "/aprender#laboratorio"),
    ("/practica/ejercicios", "/aprender/laboratorio/merge-sort"),
    ("/practica/laboratorio/programacion-dinamica?n=10", "/aprender/laboratorio/programacion-dinamica?n=10"),
    ("/practica/laboratorio/backtracking", "/aprender/laboratorio/backtracking"),
    ("/practica/laboratorio/voraz", "/aprender/laboratorio/voraz"),
    ("/practica/laboratorio/kruskal", "/aprender/laboratorio/kruskal"),
])
def test_urls_antiguas_de_practicar_redirigen(cliente, antigua, nueva):
    respuesta = cliente.get(antigua)
    assert respuesta.status_code == 301
    assert respuesta.headers["Location"].endswith(nueva)


def test_indice_del_laboratorio_lleva_a_la_seccion_de_aprender(cliente):
    registrar(cliente)
    respuesta = cliente.get("/aprender/laboratorio")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/aprender#laboratorio")
    respuesta = cliente.get("/aprender/laboratorio/no-existe")
    assert respuesta.headers["Location"].endswith("/aprender#laboratorio")


def test_no_hay_enlaces_internos_rotos(cliente, respuestas_correctas):
    registrar(cliente)
    completar_unidad(cliente, respuestas_correctas["01"])
    pendientes, visitadas = ["/", "/aprender", "/progreso", "/ajustes"], set()
    while pendientes:
        url = pendientes.pop()
        if url in visitadas or url.startswith(("/logout", "/static")):
            continue
        visitadas.add(url)
        respuesta = cliente.get(url, follow_redirects=True)
        assert respuesta.status_code == 200, url
        pendientes.extend(enlaces(respuesta.get_data(as_text=True)))
    assert any(url.startswith("/aprender/laboratorio/") for url in visitadas)
    assert "/aprender/ruta/02" in visitadas
