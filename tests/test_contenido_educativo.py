import pytest

from services.algoritmos.kruskal import kruskal
from services.algoritmos.prim import prim
from services.algoritmos.union_find import UnionFind
from services.algoritmos.catalogo import GRAFO_EJEMPLO, EDUCATIVOS, COMPARACION_MST


def test_kruskal_encuentra_arbol_minimo_del_ejemplo():
    aristas, costo, pasos = kruskal(**GRAFO_EJEMPLO)
    assert len(aristas) == len(GRAFO_EJEMPLO['vertices']) - 1
    assert costo == 10
    assert any('ciclo' in paso['decision'] for paso in pasos)


def test_prim_encuentra_arbol_minimo_del_ejemplo():
    aristas, costo, pasos = prim(**GRAFO_EJEMPLO, inicio='A')
    assert len(aristas) == len(GRAFO_EJEMPLO['vertices']) - 1
    assert costo == 10
    assert pasos


def test_prim_y_kruskal_obtienen_el_mismo_costo():
    assert kruskal(**GRAFO_EJEMPLO)[1] == prim(**GRAFO_EJEMPLO, inicio='A')[1]


def test_union_find_une_y_detecta_conjuntos():
    uf = UnionFind(['A', 'B', 'C'])
    assert uf.union('A', 'B') is True
    assert uf.connected('A', 'B') is True
    assert uf.connected('A', 'C') is False
    assert uf.union('A', 'B') is False


def test_algoritmos_rechazan_grafo_no_conexo():
    vertices = ['A', 'B', 'C']
    aristas = [('A', 'B', 2)]
    with pytest.raises(ValueError):
        kruskal(vertices, aristas)
    with pytest.raises(ValueError):
        prim(vertices, aristas, inicio='A')


def test_catalogo_contiene_las_tres_lecciones_y_comparacion():
    assert {item['slug'] for item in EDUCATIVOS} == {'kruskal', 'prim', 'union-find'}
    assert COMPARACION_MST
