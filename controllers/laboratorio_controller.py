import inspect

from flask import Blueprint, render_template, redirect, request, url_for, session

from repositories.exercise_repository import ExerciseRepository
from repositories.progress_repository import ProgressRepository
from services.algoritmos import catalogo
from services.algoritmos.backtracking import conflicto_reina, resolver_reinas
from services.algoritmos.merge_sort import CRITERIOS, ordenar_ejercicios
from services.algoritmos.voraz import pendientes, prioridad, recomendar_siguiente
from services.algoritmos.programacion_dinamica import (
    N_MAXIMO,
    comparar_escaleras,
    escaleras_memoizado,
    validar_n,
)

# El Laboratorio de algoritmos forma parte de la sección Aprender: sus páginas
# viven bajo /aprender/laboratorio y su índice es la sección "Laboratorio de
# algoritmos" de /aprender. Las antiguas URL de Practicar redirigen aquí.
laboratorio_bp = Blueprint('laboratorio', __name__)


def _seccion_laboratorio():
    return redirect(url_for('aprender.mostrar_aprender', _anchor='laboratorio'))


@laboratorio_bp.route('/aprender/laboratorio')
def indice():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return _seccion_laboratorio()


@laboratorio_bp.route('/aprender/laboratorio/merge-sort')
def ejercicios_ordenados():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    criterio = request.args.get('orden', 'dificultad')
    if criterio not in CRITERIOS:
        criterio = 'dificultad'

    ejercicios = [
        {**ejercicio, 'orden_original': posicion}
        for posicion, ejercicio in enumerate(ExerciseRepository().find_all(), start=1)
    ]
    resultado = ordenar_ejercicios(ejercicios, criterio)

    return render_template(
        'laboratorio/ejercicios.html',
        ejercicios=resultado.elementos,
        resultado=resultado,
        criterio=criterio,
        criterios=[(clave, nombre) for clave, (nombre, _) in CRITERIOS.items()],
    )


@laboratorio_bp.route('/aprender/laboratorio/programacion-dinamica')
def laboratorio_programacion_dinamica():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    error = None
    estado = 200
    try:
        n = validar_n(request.args.get('n', '8'))
    except ValueError as exc:
        error, n, estado = str(exc), 8, 400

    return render_template(
        'laboratorio/programacion_dinamica.html',
        r=comparar_escaleras(n),
        n_maximo=N_MAXIMO,
        error=error,
        codigo=inspect.getsource(escaleras_memoizado),
    ), estado


@laboratorio_bp.route('/aprender/laboratorio/backtracking')
def laboratorio_backtracking():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    error = None
    estado = 200
    try:
        numero = int(request.args.get('solucion', '1'))
        if numero not in (1, 2):  # el tablero de 4 x 4 tiene exactamente 2 soluciones
            raise ValueError
    except ValueError:
        error, numero, estado = 'Elige la solución 1 o la solución 2.', 1, 400

    return render_template(
        'laboratorio/backtracking.html',
        r=resolver_reinas(4, numero),
        error=error,
        codigo=inspect.getsource(conflicto_reina) + '\n\n' + inspect.getsource(resolver_reinas),
    ), estado


@laboratorio_bp.route('/aprender/laboratorio/voraz')
def laboratorio_voraz():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    preguntas = ExerciseRepository().find_quiz_questions(
        session['usuario'].get('id_persona'), ProgressRepository()
    )
    elegida = recomendar_siguiente(preguntas)
    candidatos = [
        {'pregunta': item, 'prioridad': prioridad(item),
         'elegida': elegida is not None and item['id_ejercicio'] == elegida['id_ejercicio']}
        for item in pendientes(preguntas)
    ]
    return render_template(
        'laboratorio/voraz.html',
        recomendacion=elegida,
        candidatos=candidatos,
        total=len(preguntas),
        correctas=sum(1 for item in preguntas if item['estado'] == 'correcto'),
        codigo=inspect.getsource(prioridad) + '\n\n' + inspect.getsource(recomendar_siguiente),
    )


@laboratorio_bp.route('/aprender/laboratorio/<slug>')
def laboratorio_educativo(slug):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    from services.algoritmos.catalogo import EDUCATIVOS, COMPARACION_MST, GRAFO_EJEMPLO
    from services.algoritmos.kruskal import kruskal
    from services.algoritmos.prim import prim
    from services.algoritmos.union_find import UnionFind

    contenido = next((item for item in EDUCATIVOS if item['slug'] == slug), None)
    if contenido is None:
        return _seccion_laboratorio()

    if slug == 'kruskal':
        aristas, costo, pasos = kruskal(**GRAFO_EJEMPLO)
        codigo = inspect.getsource(kruskal)
    elif slug == 'prim':
        aristas, costo, pasos = prim(**GRAFO_EJEMPLO, inicio='A')
        codigo = inspect.getsource(prim)
    else:
        estructura = UnionFind(['A', 'B', 'C'])
        estructura.union('A', 'B')
        aristas, costo, pasos = [], 0, [
            {'arista': ('A', 'B', '—'), 'decision': 'Union(A, B): combina los conjuntos'},
            {'arista': ('A', 'B', '—'), 'decision': f"Find(A) = {estructura.find('A')} y Find(B) = {estructura.find('B')}"},
            {'arista': ('A', 'C', '—'), 'decision': f"Find(C) = {estructura.find('C')}; C sigue separado"},
        ]
        codigo = inspect.getsource(UnionFind)

    return render_template(
        'laboratorio/educativo.html', contenido=contenido, codigo=codigo,
        aristas=aristas, costo=costo, pasos=pasos,
        grafo=GRAFO_EJEMPLO, comparacion=COMPARACION_MST,
    )


# --- Compatibilidad con las URL de la antigua sección Practicar ---------------

@laboratorio_bp.route('/practica')
@laboratorio_bp.route('/practica/laboratorio')
def practica_obsoleta():
    return redirect(url_for('aprender.mostrar_aprender', _anchor='laboratorio'), code=301)


@laboratorio_bp.route('/practica/ejercicios')
def ejercicios_obsoletos():
    return redirect(url_for('laboratorio.ejercicios_ordenados', **request.args), code=301)


@laboratorio_bp.route('/practica/laboratorio/<path:destino>')
def laboratorio_obsoleto(destino):
    url = f"/aprender/laboratorio/{destino}"
    if request.query_string:
        url += "?" + request.query_string.decode("utf-8", "ignore")
    return redirect(url, code=301)
