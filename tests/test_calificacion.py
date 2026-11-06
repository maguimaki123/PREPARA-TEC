"""Casos de prueba de la sección 8.1 del documento."""
import copy
from decimal import Decimal

import pytest

from calificacion import (Respuesta, calificar, cargar_semilla, puntaje_maximo,
                          reglas_desde_perfil, validar_perfil)

AREAS_UNJFSC = ("COMUNICACION", "MATEMATICA", "CTA", "CIENCIAS_SOCIALES")


def armar(area, correctas, incorrectas, blancos):
    out = [Respuesta(area, "A", "A") for _ in range(correctas)]
    out += [Respuesta(area, "A", "B") for _ in range(incorrectas)]
    out += [Respuesta(area, "A", None) for _ in range(blancos)]
    return out


@pytest.fixture
def unab():
    return cargar_semilla("unab")


@pytest.fixture
def unjfsc():
    return cargar_semilla("unjfsc")


# ---------- UNAB ----------
@pytest.mark.parametrize(
    "id_caso, c, i, b, esperado, alcanza",
    [
        ("UNAB-01", 40, 15, 5, "791.5625", True),
        ("UNAB-02", 60, 0, 0, "1200", True),
        ("UNAB-03", 25, 20, 15, "488.75", False),
        ("UNAB-04", 26, 20, 14, "508.75", True),
        ("UNAB-05", 0, 60, 0, "-33.75", False),
        ("UNAB-06", 20, 10, 30, "394.375", False),   # examen interrumpido
        ("UNAB-07", 0, 0, 60, "0", False),
    ],
)
def test_unab(unab, id_caso, c, i, b, esperado, alcanza):
    res = calificar(armar("GENERAL", c, i, b), reglas_desde_perfil(unab))
    assert res.puntaje == Decimal(esperado), id_caso
    assert res.alcanza_minimo is alcanza
    assert (res.correctas, res.incorrectas, res.blancos) == (c, i, b)


def test_unab_borde_exactamente_500_alcanza_minimo(unab):
    res = calificar(armar("GENERAL", 25, 0, 35), reglas_desde_perfil(unab))
    assert res.puntaje == Decimal("500") and res.alcanza_minimo is True


# ---------- UNJFSC ----------
def examen_unjfsc():
    """45 correctas (15, 10, 12, 8), 20 incorrectas y 15 blancos; 20 por área."""
    return (armar("COMUNICACION", 15, 5, 0) + armar("MATEMATICA", 10, 5, 5)
            + armar("CTA", 12, 5, 3) + armar("CIENCIAS_SOCIALES", 8, 5, 7))


@pytest.mark.parametrize("id_caso, grupo, esperado",
                         [("UNJ-01", "A", "112"), ("UNJ-02", "B", "114"),
                          ("UNJ-03", "C", "114"), ("UNJ-04", "D", "107")])
def test_unjfsc_por_grupo(unjfsc, id_caso, grupo, esperado):
    examen = examen_unjfsc()
    assert len(examen) == 80
    res = calificar(examen, reglas_desde_perfil(unjfsc, grupo))
    assert res.puntaje == Decimal(esperado), id_caso
    assert (res.correctas, res.incorrectas, res.blancos) == (45, 20, 15)
    assert res.alcanza_minimo is True


def test_unjfsc_maximo_grupo_a_es_200(unjfsc):     # UNJ-05
    examen = [r for a in AREAS_UNJFSC for r in armar(a, 20, 0, 0)]
    assert calificar(examen, reglas_desde_perfil(unjfsc, "A")).puntaje == Decimal("200")
    assert puntaje_maximo(unjfsc, "A") == Decimal("200")


def test_unjfsc_todo_en_blanco_es_cero(unjfsc):    # UNJ-06
    examen = [r for a in AREAS_UNJFSC for r in armar(a, 0, 0, 20)]
    res = calificar(examen, reglas_desde_perfil(unjfsc, "A"))
    assert res.puntaje == Decimal("0") and res.alcanza_minimo is False


def test_unjfsc_exige_grupo_valido(unjfsc):
    with pytest.raises(ValueError):
        reglas_desde_perfil(unjfsc, "Z")
    with pytest.raises(ValueError):
        reglas_desde_perfil(unjfsc)          # sin grupo


def test_puntaje_maximo_unab(unab):
    assert puntaje_maximo(unab) == Decimal("1200")


# ---------- Reglas editables desde la interfaz ----------
def test_cambiar_penalizacion_cambia_el_resultado(unab):          # EDIT-01
    nuevo = copy.deepcopy(unab)
    nuevo["penalizacion"]["valor"] = "1"
    nuevo["version"] = 2
    res = calificar(armar("GENERAL", 40, 15, 5), reglas_desde_perfil(nuevo))
    assert res.puntaje == Decimal("785")


def test_version_anterior_no_cambia(unab):                         # EDIT-02
    reglas_v1 = reglas_desde_perfil(unab)
    nuevo = copy.deepcopy(unab)
    nuevo["penalizacion"]["valor"] = "1"
    reglas_desde_perfil(nuevo)
    res = calificar(armar("GENERAL", 40, 15, 5), reglas_v1)
    assert res.puntaje == Decimal("791.5625") and reglas_v1.version == 1


def test_penalizacion_proporcional(unab):                          # EDIT-03
    nuevo = copy.deepcopy(unab)
    nuevo["penalizacion"] = {"modo": "PROPORCIONAL", "valor": "0.25"}   # un cuarto de 20 = 5
    res = calificar(armar("GENERAL", 40, 12, 8), reglas_desde_perfil(nuevo))
    assert res.puntaje == Decimal("740")


def test_puntos_por_pregunta_en_blanco(unab):                      # EDIT-04
    nuevo = copy.deepcopy(unab)
    nuevo["puntos_blanco"] = "1"
    res = calificar(armar("GENERAL", 10, 5, 5), reglas_desde_perfil(nuevo))
    assert res.puntaje == Decimal("202.1875")


def test_redondeo_a_dos_decimales(unab):                           # EDIT-05
    nuevo = copy.deepcopy(unab)
    nuevo["decimales"] = 2
    assert calificar(armar("GENERAL", 40, 15, 5), reglas_desde_perfil(nuevo)).puntaje == Decimal("791.56")
    assert calificar(armar("GENERAL", 25, 1, 34), reglas_desde_perfil(nuevo)).puntaje == Decimal("499.44")


def test_truncar_en_cero(unab):                                    # EDIT-06
    nuevo = copy.deepcopy(unab)
    nuevo["truncar_en_cero"] = True
    assert calificar(armar("GENERAL", 0, 60, 0), reglas_desde_perfil(nuevo)).puntaje == Decimal("0")


def test_nuevo_perfil_creado_desde_cero():                         # EDIT-07
    perfil = {"nombre": "Simulacro propio", "version": 1,
              "areas": [{"codigo": "LOGICA", "nombre": "Lógica", "nro_preguntas": 10, "puntos": "2.5"}],
              "grupos": [], "penalizacion": {"modo": "FIJA", "valor": "0.5"},
              "puntos_blanco": "0", "puntaje_minimo": "10"}
    assert validar_perfil(perfil) == []
    res = calificar(armar("LOGICA", 6, 2, 2), reglas_desde_perfil(perfil))
    assert res.puntaje == Decimal("14")          # 6*2.5 - 2*0.5
    assert res.alcanza_minimo is True


# ---------- Validación del perfil (pantalla de edición) ----------
def test_perfil_valido_no_da_errores(unab, unjfsc):
    assert validar_perfil(unab) == [] and validar_perfil(unjfsc) == []


def test_validacion_detecta_grupo_sin_puntos(unjfsc):              # VAL-01
    malo = copy.deepcopy(unjfsc)
    del malo["areas"][0]["puntos"]["B"]
    assert any("grupo 'B'" in e for e in validar_perfil(malo))
    with pytest.raises(ValueError):
        reglas_desde_perfil(malo, "B")


def test_validacion_detecta_valores_negativos_y_modo(unab):        # VAL-02
    malo = copy.deepcopy(unab)
    malo["areas"][0]["puntos"] = "-5"
    malo["penalizacion"]["modo"] = "OTRA"
    errores = validar_perfil(malo)
    assert any("negativos" in e for e in errores)
    assert any("FIJA o PROPORCIONAL" in e for e in errores)


def test_validacion_detecta_numero_invalido(unab):                 # VAL-03
    malo = copy.deepcopy(unab)
    malo["puntaje_minimo"] = "abc"
    assert any("puntaje mínimo" in e for e in validar_perfil(malo))


# ---------- Generales ----------
def test_area_sin_regla_lanza_error(unab):
    with pytest.raises(ValueError):
        calificar([Respuesta("OTRA", "A", "A")], reglas_desde_perfil(unab))


def test_resultado_es_decimal_exacto_no_flotante(unab):
    res = calificar(armar("GENERAL", 0, 3, 0), reglas_desde_perfil(unab))
    assert isinstance(res.puntaje, Decimal) and res.puntaje == Decimal("-1.6875")


def test_mismo_examen_mismo_puntaje(unjfsc):
    examen, reglas = examen_unjfsc(), reglas_desde_perfil(unjfsc, "A")
    assert calificar(examen, reglas) == calificar(list(reversed(examen)), reglas)
