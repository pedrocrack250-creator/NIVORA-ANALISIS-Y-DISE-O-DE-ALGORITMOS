from flask import Blueprint, render_template, redirect, url_for, session, request
from models.ruta_model import RutaModel
from repositories.exercise_repository import ExerciseRepository
from repositories.progress_repository import ProgressRepository
from services import progreso_service, recomendacion_service
from services.algoritmos import catalogo
from services.auth_service import AuthService

aprender_bp = Blueprint('aprender', __name__)
auth_service = AuthService()
progress_repository = ProgressRepository()


def _siguiente_pregunta(actividades):
    """Algoritmo voraz sobre el progreso real del estudiante (ver recomendacion_service)."""
    preguntas = ExerciseRepository().find_quiz_questions(
        session['usuario'].get('id_persona'), progress_repository
    )
    return recomendacion_service.siguiente_pregunta(
        preguntas, RutaModel.obtener_unidades(), RutaModel.obtener_lecciones(), actividades
    )


def _actividades():
    """Registros de progreso del usuario: se cargan de PROGRESO_LECCION al
    iniciar sesión y se mantienen sincronizados en cada cambio."""
    return session.get('progreso', {})


@aprender_bp.route('/aprender')
def mostrar_aprender():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    actividades = _actividades()
    rutas = RutaModel.obtener_rutas(actividades)
    # La recomendación inicial solo orienta antes de empezar: desaparece en
    # cuanto existe un registro de cualquier lección (abrirla ya lo crea).
    mostrar_recomendacion = (
        bool(session['usuario'].get('recomendacion'))
        and not progreso_service.inicio_alguna_leccion(actividades)
    )

    return render_template(
        'aprender.html',
        rutas=rutas,
        usuario=session['usuario']['nombre'],
        mostrar_recomendacion=mostrar_recomendacion,
        # Una vez iniciado el estudio, el algoritmo voraz propone la siguiente pregunta.
        siguiente_pregunta=(
            None if mostrar_recomendacion else _siguiente_pregunta(actividades)
        ),
        laboratorio_interactivos=catalogo.INTERACTIVOS,
        laboratorio_educativos=catalogo.EDUCATIVOS,
    )


@aprender_bp.route('/aprender/leccion/variables')
def leccion_variables():
    # Ruta histórica de la primera lección: aplica las mismas reglas que el
    # resto (acceso y registro de inicio).
    return leccion('variables')


@aprender_bp.route('/aprender/ruta/<route_id>')
def ruta(route_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    actividades = _actividades()
    unidad = RutaModel.obtener_ruta(route_id, actividades)
    if unidad is None or not unidad['desbloqueada']:
        return redirect(url_for('aprender.mostrar_aprender'))

    unidades = RutaModel.obtener_unidades()
    todas = RutaModel.obtener_lecciones()
    lecciones = [
        {
            **lesson,
            'completada': progreso_service.leccion_completada(actividades, lesson['id']),
            'intentada': progreso_service.leccion_intentada(actividades, lesson['id']),
            'desbloqueada': progreso_service.leccion_desbloqueada(unidades, todas, lesson, actividades),
        }
        for lesson in progreso_service.lecciones_de_unidad(todas, unidad['id_unidad'])
    ]
    return render_template(
        'ruta.html',
        ruta_id=route_id,
        unidad=unidad,
        lecciones=lecciones,
    )


def _contexto_leccion(lesson):
    unidad = next(
        route for route in RutaModel.obtener_rutas(_actividades())
        if route['id_unidad'] == lesson['unidad']
    )
    return {'lesson': lesson, 'unidad': unidad}


@aprender_bp.route('/aprender/leccion/<lesson_id>', methods=['GET'])
def leccion(lesson_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(url_for('aprender.mostrar_aprender'))

    actividades = _actividades()
    unidades = RutaModel.obtener_unidades()
    lecciones = RutaModel.obtener_lecciones()
    if not progreso_service.leccion_desbloqueada(unidades, lecciones, lesson, actividades):
        if progreso_service.unidad_desbloqueada(unidades, lecciones, lesson['unidad'], actividades):
            return redirect(url_for('aprender.ruta', route_id=f"{lesson['unidad']:02d}"))
        return redirect(url_for('aprender.mostrar_aprender'))

    # Abrir la lección la marca como iniciada (BD y sesión) sin tocar su avance.
    if lesson_id not in actividades:
        progress_repository.mark_started(session['usuario'].get('id_persona'), lesson_id)
        session.setdefault('progreso', {})[lesson_id] = {
            'iniciada': True, 'completada': False, 'intentada': False,
            'puntuacion': 0, 'total': 0,
        }
        session.modified = True

    return render_template('leccion.html', resultado=None, **_contexto_leccion(lesson))


@aprender_bp.route('/aprender/leccion/<lesson_id>/completar', methods=['POST'])
def completar_leccion(lesson_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(url_for('aprender.mostrar_aprender'))
    unidades = RutaModel.obtener_unidades()
    lecciones = RutaModel.obtener_lecciones()
    if not progreso_service.leccion_desbloqueada(unidades, lecciones, lesson, _actividades()):
        return redirect(url_for('aprender.mostrar_aprender'))

    answers = [request.form.get(f'respuesta_{number}', '') for number in range(1, 4)]
    results = [answer == correct for answer, correct in zip(answers, lesson['answers'])]
    score, total = sum(results), len(lesson['answers'])
    progreso = session.setdefault('progreso', {})
    progreso[lesson_id] = {
        'iniciada': True,
        'completada': score == total,
        'intentada': True,
        'puntuacion': score,
        'total': total,
    }
    user_id = session['usuario'].get('id_persona')
    progress_repository.save_activity(user_id, lesson_id, progreso[lesson_id])
    # Guardar cada respuesta por separado para que el recomendador Voraz use
    # intentos y errores reales, sin alterar el progreso general de la lección.
    for exercise_id, is_correct in zip(lesson.get('exercise_ids', []), results):
        progress_repository.save_exercise_attempt(user_id, exercise_id, is_correct)
    session.modified = True
    next_lesson = progreso_service.siguiente_leccion(unidades, lecciones, lesson, progreso)
    return render_template('leccion.html', resultado={
        'score': score, 'total': total, 'results': results, 'answers': answers,
        'completada': score == total, 'next_lesson': next_lesson
    }, siguiente_pregunta=_siguiente_pregunta(progreso), **_contexto_leccion(lesson))
