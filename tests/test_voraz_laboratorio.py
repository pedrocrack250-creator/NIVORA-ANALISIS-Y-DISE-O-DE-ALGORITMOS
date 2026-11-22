import pytest

from app import create_app
from config import TestingConfig
from services.algoritmos.voraz import pendientes, prioridad, recomendar_siguiente


def pregunta(id_ejercicio, estado="pendiente", errores=0, dificultad="basico", numero=1):
    return {"id_ejercicio": id_ejercicio, "estado": estado, "errores": errores,
            "dificultad": dificultad, "numero": numero}


# --- La regla extraída es la misma que ya se usaba -------------------------------

def test_prioridad_ordena_errores_dificultad_posicion_e_id():
    assert prioridad(pregunta(9, errores=2, dificultad="avanzado", numero=3)) == (-2, 3, 3, 9)
    assert prioridad(pregunta(1, errores=3)) < prioridad(pregunta(2, errores=1))
    assert prioridad(pregunta(1, dificultad="basico")) < prioridad(pregunta(2, dificultad="intermedio"))
    assert prioridad(pregunta(1, numero=1)) < prioridad(pregunta(2, numero=2))
    assert prioridad(pregunta(1)) < prioridad(pregunta(2))


def test_dificultad_desconocida_tiene_la_menor_prioridad():
    assert prioridad(pregunta(1, dificultad="rara")) > prioridad(pregunta(2, dificultad="avanzado"))


def test_pendientes_excluye_solo_las_correctas():
    items = [pregunta(1, "correcto"), pregunta(2, "incorrecto", 1), pregunta(3)]
    assert [e["id_ejercicio"] for e in pendientes(items)] == [2, 3]


def test_recomendar_coincide_con_el_minimo_de_la_prioridad():
    items = [pregunta(1, errores=1, numero=2), pregunta(2, errores=3, dificultad="avanzado"), pregunta(3, errores=3, numero=1)]
    assert recomendar_siguiente(items)["id_ejercicio"] == 3
    assert recomendar_siguiente(items) == min(pendientes(items), key=prioridad)


def test_sin_pendientes_no_recomienda():
    assert recomendar_siguiente([]) is None
    assert recomendar_siguiente([pregunta(1, "correcto")]) is None


# --- Página del laboratorio -----------------------------------------------------

@pytest.fixture
def cliente():
    return create_app(TestingConfig).test_client()


def iniciar_sesion(cliente, id_persona=1):
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        sesion["usuario"] = {"id_persona": id_persona, "nombre": "Ana"}


def responder(cliente, leccion, respuestas):
    with cliente.session_transaction() as sesion:
        datos = {"csrf_token": sesion["csrf_token"]}
    datos.update({f"respuesta_{i}": v for i, v in enumerate(respuestas, start=1)})
    return cliente.post(f"/aprender/leccion/{leccion}/completar", data=datos)


def test_requiere_login(cliente):
    respuesta = cliente.get("/aprender/laboratorio/voraz")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/login")


def test_aparece_en_el_indice_entre_los_interactivos(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender").get_data(as_text=True)
    assert "/aprender/laboratorio/voraz" in html
    # Se busca el enlace dentro de la sección del laboratorio (el panel de recomendación
    # de Aprender también enlaza a esta página, antes de esa sección).
    inicio = html.index("Algoritmos interactivos")
    assert inicio < html.index("/aprender/laboratorio/voraz", inicio) < html.index("Contenido educativo")


def test_la_ruta_propia_no_la_captura_la_ruta_educativa(cliente):
    iniciar_sesion(cliente)
    assert cliente.get("/aprender/laboratorio/voraz").status_code == 200
    assert cliente.get("/aprender/laboratorio/kruskal").status_code == 200
    assert cliente.get("/aprender/laboratorio/no-existe").status_code == 302


def test_estudiante_nuevo_ve_la_primera_pregunta_y_la_explicacion(cliente):
    iniciar_sesion(cliente)
    html = cliente.get("/aprender/laboratorio/voraz").get_data(as_text=True)
    assert "heurística de selección local" in html
    assert "O(n)" in html
    assert "def recomendar_siguiente" in html and "def prioridad" in html
    assert "Variables y tipos de datos · pregunta 1" in html
    assert "← elegida" in html
    assert "Has respondido bien <strong>0</strong> de <strong>48</strong>" in html


def test_la_pagina_usa_el_progreso_real_del_quiz(cliente):
    iniciar_sesion(cliente)
    responder(cliente, "variables", ["nombre", "str", "True"])  # solo falla la pregunta 2
    html = cliente.get("/aprender/laboratorio/voraz").get_data(as_text=True)
    assert "Has respondido bien <strong>2</strong> de <strong>48</strong>" in html
    assert "<h2>Variables y tipos de datos · pregunta 2</h2>" in html  # la fallada sube
    assert "Respuestas incorrectas: 1" in html
    assert html.count("← elegida") == 1
    assert "¿Qué tipo de dato es 20?" in html


def test_al_terminar_la_unidad_01_recomienda_la_unidad_02(cliente, respuestas_correctas):
    iniciar_sesion(cliente)
    for leccion, respuestas in respuestas_correctas["01"].items():
        responder(cliente, leccion, respuestas)
    html = cliente.get("/aprender/laboratorio/voraz").get_data(as_text=True)
    assert "Has respondido bien <strong>12</strong> de <strong>48</strong>" in html
    assert "<h2>Condicionales if y else · pregunta 1</h2>" in html


def test_sin_pendientes_muestra_mensaje(cliente, respuestas_correctas):
    iniciar_sesion(cliente)
    for unidad in respuestas_correctas.values():
        for leccion, respuestas in unidad.items():
            responder(cliente, leccion, respuestas)
    html = cliente.get("/aprender/laboratorio/voraz").get_data(as_text=True)
    assert "No hay preguntas pendientes" in html
    assert "← elegida" not in html
