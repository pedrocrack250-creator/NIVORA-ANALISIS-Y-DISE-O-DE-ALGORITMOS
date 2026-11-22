"""Algoritmos del curso aplicados al funcionamiento real de Nivora.

Merge Sort ordena las unidades (desbloqueo) y las lecciones por repasar; el
algoritmo voraz recomienda la siguiente pregunta con el progreso real. Cada
prueba crea su propia aplicación con base SQLite temporal.
"""
import pytest

from app import create_app
from config import TestingConfig
from services import progreso_service, recomendacion_service

CORREO = "ana@example.com"
CLAVE = "password-123"


# --- Utilidades ---------------------------------------------------------------

@pytest.fixture
def cliente():
    return create_app(TestingConfig).test_client()


def csrf(cliente):
    with cliente.session_transaction() as sesion:
        token = sesion.get("csrf_token")
    if token is None:
        cliente.get("/login")
        with cliente.session_transaction() as sesion:
            token = sesion["csrf_token"]
    return token


def registrar(cliente):
    cliente.get("/registro")
    cliente.post("/registro", data={
        "csrf_token": csrf(cliente), "nombre": "Ana", "email": CORREO, "password": CLAVE,
    })
    cliente.post("/nivel", data={"csrf_token": csrf(cliente), "nivel_inicial": "no_se_nada"})


def responder(cliente, leccion, respuestas):
    cliente.get(f"/aprender/leccion/{leccion}")
    datos = {"csrf_token": csrf(cliente)}
    datos.update({f"respuesta_{i}": v for i, v in enumerate(respuestas, start=1)})
    return cliente.post(f"/aprender/leccion/{leccion}/completar", data=datos)


def leccion(id_, numero, unidad=1):
    return {"id": id_, "numero": numero, "unidad": unidad, "titulo": id_.capitalize()}


def pregunta(lesson_id, numero=1, id_ejercicio=1, errores=0, estado="pendiente"):
    return {"id_ejercicio": id_ejercicio, "lesson_id": lesson_id, "lesson_title": lesson_id.capitalize(),
            "numero": numero, "pregunta": f"¿{lesson_id} {numero}?", "dificultad": "basico",
            "estado": estado, "errores": errores, "intentos": errores}


# --- Merge Sort en el núcleo: orden de unidades y desbloqueo -------------------

def test_estado_unidades_ejecuta_merge_sort(monkeypatch):
    llamadas = []
    original = progreso_service.merge_sort

    def espia(elementos, clave=None, etiqueta=None):
        llamadas.append(len(elementos))
        return original(elementos, clave=clave, etiqueta=etiqueta)

    monkeypatch.setattr(progreso_service, "merge_sort", espia)
    unidades = [{"id_unidad": 1, "numero": 1}, {"id_unidad": 2, "numero": 2}]
    progreso_service.estado_unidades(unidades, [], {})
    assert llamadas == [2]


def test_las_unidades_se_ordenan_aunque_lleguen_desordenadas():
    unidades = [{"id_unidad": 3, "numero": 3}, {"id_unidad": 1, "numero": 1}, {"id_unidad": 2, "numero": 2}]
    lecciones = [leccion("a", 1, 1), leccion("b", 2, 2), leccion("c", 3, 3)]
    estados = progreso_service.estado_unidades(unidades, lecciones, {})
    assert [e["id_unidad"] for e in estados] == [1, 2, 3]
    assert [e["desbloqueada"] for e in estados] == [True, False, False]


def test_el_desbloqueo_sigue_el_orden_de_las_unidades():
    unidades = [{"id_unidad": 2, "numero": 2}, {"id_unidad": 1, "numero": 1}]
    lecciones = [leccion("a", 1, 1), leccion("b", 2, 2)]
    actividades = {"a": {"completada": True, "intentada": True}}
    estados = {e["id_unidad"]: e for e in progreso_service.estado_unidades(unidades, lecciones, actividades)}
    assert estados[1]["completa"] and estados[2]["desbloqueada"]


# --- Merge Sort: lecciones para repasar ---------------------------------------

def test_repaso_ordena_de_menor_a_mayor_acierto():
    lecciones = [leccion("a", 1), leccion("b", 2), leccion("c", 3)]
    actividades = {
        "a": {"intentada": True, "completada": False, "puntuacion": 2, "total": 3},
        "b": {"intentada": True, "completada": False, "puntuacion": 0, "total": 3},
        "c": {"intentada": True, "completada": False, "puntuacion": 1, "total": 3},
    }
    repaso = progreso_service.lecciones_para_repasar(lecciones, actividades)
    assert [item["id"] for item in repaso] == ["b", "c", "a"]
    assert [item["porcentaje"] for item in repaso] == [0, 33, 67]


def test_repaso_es_estable_a_igual_acierto_conserva_el_orden_de_la_ruta():
    lecciones = [leccion("a", 1), leccion("b", 2), leccion("c", 3)]
    igual = {"intentada": True, "completada": False, "puntuacion": 1, "total": 3}
    repaso = progreso_service.lecciones_para_repasar(lecciones, {"c": igual, "b": igual, "a": igual})
    assert [item["id"] for item in repaso] == ["a", "b", "c"]


def test_repaso_excluye_completadas_y_no_intentadas():
    lecciones = [leccion("a", 1), leccion("b", 2), leccion("c", 3), leccion("d", 4)]
    actividades = {
        "a": {"intentada": True, "completada": True, "puntuacion": 3, "total": 3},
        "b": {"iniciada": True, "intentada": False, "completada": False, "puntuacion": 0, "total": 0},
        "c": {"intentada": True, "completada": False, "puntuacion": 1, "total": 3},
    }
    assert [item["id"] for item in progreso_service.lecciones_para_repasar(lecciones, actividades)] == ["c"]


def test_repaso_vacio_y_registros_heredados():
    assert progreso_service.lecciones_para_repasar([], {}) == []
    assert progreso_service.lecciones_para_repasar([leccion("a", 1)], None) == []
    assert progreso_service.lecciones_para_repasar([leccion("a", 1)], {"a": True}) == []  # bool heredado = completada


def test_repaso_ejecuta_merge_sort(monkeypatch):
    llamadas = []
    original = progreso_service.merge_sort
    monkeypatch.setattr(progreso_service, "merge_sort",
                        lambda e, clave=None, etiqueta=None: llamadas.append(len(e)) or original(e, clave=clave))
    actividades = {"a": {"intentada": True, "completada": False, "puntuacion": 0, "total": 3}}
    progreso_service.lecciones_para_repasar([leccion("a", 1)], actividades)
    assert llamadas == [1]


def test_progreso_no_muestra_repaso_sin_intentos(cliente):
    registrar(cliente)
    assert "Lecciones para repasar" not in cliente.get("/progreso").get_data(as_text=True)


def test_progreso_muestra_el_repaso_ordenado_por_acierto(cliente):
    registrar(cliente)
    responder(cliente, "variables", ["nombre", "int", "False"])      # 2/3
    responder(cliente, "operadores", ["x", "x", "x"])                # 0/3
    html = cliente.get("/progreso").get_data(as_text=True)
    assert "Lecciones para repasar" in html and "Merge Sort" in html
    assert html.index("Operadores y expresiones") > html.index("Lecciones para repasar")
    assert html.index("Acertaste 0 de 3 (0%)") < html.index("Acertaste 2 de 3 (67%)")


def test_progreso_deja_de_listar_la_leccion_al_completarla(cliente):
    registrar(cliente)
    responder(cliente, "variables", ["x", "x", "x"])
    assert "Acertaste 0 de 3" in cliente.get("/progreso").get_data(as_text=True)
    responder(cliente, "variables", ["nombre", "int", "True"])
    assert "Lecciones para repasar" not in cliente.get("/progreso").get_data(as_text=True)


# --- Voraz en el flujo real ----------------------------------------------------

def test_voraz_solo_recomienda_lecciones_desbloqueadas():
    unidades = [{"id_unidad": 1, "numero": 1}]
    lecciones = [leccion("a", 1), leccion("b", 2)]
    preguntas = [
        pregunta("a", numero=2, id_ejercicio=2),
        pregunta("b", numero=1, id_ejercicio=3, errores=9),  # muchos errores, pero 'b' sigue bloqueada
    ]
    elegida = recomendacion_service.siguiente_pregunta(preguntas, unidades, lecciones, {})
    assert elegida["lesson_id"] == "a"


def test_voraz_recomienda_la_mas_fallada_entre_las_accesibles():
    unidades = [{"id_unidad": 1, "numero": 1}]
    lecciones = [leccion("a", 1), leccion("b", 2)]
    actividades = {"a": {"intentada": True, "completada": False}}  # intentar 'a' desbloquea 'b'
    preguntas = [pregunta("a", 1, 1, errores=1), pregunta("b", 2, 2, errores=3)]
    elegida = recomendacion_service.siguiente_pregunta(preguntas, unidades, lecciones, actividades)
    assert (elegida["lesson_id"], elegida["numero"]) == ("b", 2)
    assert "3 veces" in elegida["motivo"] and "reforzarla" in elegida["motivo"]


def test_voraz_motivo_singular_y_sin_errores():
    unidades = [{"id_unidad": 1, "numero": 1}]
    lecciones = [leccion("a", 1)]
    uno = recomendacion_service.siguiente_pregunta([pregunta("a", errores=1)], unidades, lecciones, {})
    assert "1 vez:" in uno["motivo"]
    ninguno = recomendacion_service.siguiente_pregunta([pregunta("a")], unidades, lecciones, {})
    assert "siguiente pregunta pendiente" in ninguno["motivo"]


def test_voraz_sin_pendientes_accesibles_devuelve_none():
    unidades = [{"id_unidad": 1, "numero": 1}]
    lecciones = [leccion("a", 1)]
    assert recomendacion_service.siguiente_pregunta([], unidades, lecciones, {}) is None
    assert recomendacion_service.siguiente_pregunta(
        [pregunta("a", estado="correcto")], unidades, lecciones, {}) is None


def test_aprender_muestra_primero_la_recomendacion_inicial_no_la_voraz(cliente):
    registrar(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "data-recomendacion-inicial" in html
    assert "data-siguiente-pregunta" not in html


def test_aprender_recomienda_la_pregunta_fallada_con_progreso_real(cliente):
    registrar(cliente)
    responder(cliente, "variables", ["nombre", "str", "True"])  # falla solo la pregunta 2
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "data-siguiente-pregunta" in html and "data-recomendacion-inicial" not in html
    assert "Variables y tipos de datos · pregunta 2" in html
    assert "La respondiste mal 1 vez" in html
    assert "/aprender/laboratorio/voraz" in html


def test_aprender_avanza_cuando_se_completa_la_leccion(cliente):
    registrar(cliente)
    responder(cliente, "variables", ["nombre", "int", "True"])
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "Operadores y expresiones · pregunta 1" in html
    assert "siguiente pregunta pendiente de tu ruta" in html


def test_el_resultado_del_quiz_recomienda_que_seguir(cliente):
    registrar(cliente)
    html = responder(cliente, "variables", ["nombre", "str", "True"]).get_data(as_text=True)
    assert "Te recomendamos seguir con" in html
    assert "Variables y tipos de datos · pregunta 2" in html


def test_la_recomendacion_es_por_estudiante(cliente):
    registrar(cliente)
    responder(cliente, "variables", ["nombre", "str", "True"])
    cliente.get("/logout")
    cliente.get("/registro")
    cliente.post("/registro", data={"csrf_token": csrf(cliente), "nombre": "Luis",
                                    "email": "luis@example.com", "password": CLAVE})
    cliente.post("/nivel", data={"csrf_token": csrf(cliente), "nivel_inicial": "no_se_nada"})
    cliente.get("/aprender/leccion/variables")
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "Variables y tipos de datos · pregunta 1" in html  # sin los errores de Ana


def test_aprender_oculta_la_recomendacion_al_terminar_todo(cliente, respuestas_correctas):
    registrar(cliente)
    for unidad in respuestas_correctas.values():
        for id_leccion, valores in unidad.items():
            responder(cliente, id_leccion, valores)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "data-siguiente-pregunta" not in html
