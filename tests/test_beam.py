import math
from beam import Viga, calcular_reacciones_viga, centro_de_masa_viga


def test_reacciones_puntual():
    v = Viga(longitud=10.0)
    v.agregar_carga_puntual(5.0, 10.0)
    ra, rb, rc = calcular_reacciones_viga(v)
    assert math.isclose(ra, 5.0, rel_tol=1e-6)
    assert math.isclose(rb, 5.0, rel_tol=1e-6)
    assert math.isclose(rc, 0.0, rel_tol=1e-6)


def test_centro_de_masa():
    v = Viga(longitud=8.0)
    v.agregar_carga_puntual(2.0, 4.0)
    v.agregar_carga_puntual(6.0, 8.0)
    cm = centro_de_masa_viga(v)
    expected = (2.0*4.0 + 6.0*8.0) / (4.0 + 8.0)
    assert math.isclose(cm, expected, rel_tol=1e-6)
