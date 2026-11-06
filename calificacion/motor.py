"""Motor de calificación.

Función pura: recibe respuestas y reglas, devuelve el puntaje. No accede a base
de datos ni a pantallas. Usa Decimal para que valores como 0,5625 y 0,1 se
calculen de forma exacta (RNF-01).

Las reglas NO están escritas en el código: se construyen a partir de un
"perfil" (diccionario / JSON) que el super administrador edita desde la
interfaz y que la aplicación guarda en la base de datos. Ver `reglas_desde_perfil`.

Formato del perfil
------------------
{
  "nombre": "...", "version": 3,
  "areas": [ {"codigo": "MATEMATICA", "nombre": "...", "nro_preguntas": 20,
              "puntos": "4"  |  {"A": "4", "B": "3"} } ],
  "grupos": ["A", "B"],                 # vacío si el perfil no usa grupos
  "penalizacion": {"modo": "FIJA", "valor": "0.1"},
       # FIJA: puntos que resta cada incorrecta.
       # PROPORCIONAL: fracción de los puntos de esa pregunta (0.25 = un cuarto).
  "puntos_blanco": "0",                 # puntos por pregunta en blanco
  "puntaje_minimo": "11",
  "truncar_en_cero": false,             # si el puntaje negativo se lleva a 0
  "decimales": null                     # redondeo del puntaje final (null = exacto)
}
"""
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional

MODOS_PENALIZACION = ("FIJA", "PROPORCIONAL")


@dataclass(frozen=True)
class Respuesta:
    """Una pregunta del examen y lo que marcó el estudiante.

    marcada = None significa pregunta en blanco. En un examen interrumpido,
    las preguntas sin respuesta registrada se pasan con marcada=None.
    """
    area: str
    correcta: str
    marcada: Optional[str] = None


@dataclass(frozen=True)
class Reglas:
    """Reglas ya resueltas para un grupo concreto (inmutables)."""
    nombre: str
    version: int
    puntos_por_area: Dict[str, Decimal]
    penalizacion_modo: str
    penalizacion_valor: Decimal
    puntos_blanco: Decimal
    puntaje_minimo: Decimal
    truncar_en_cero: bool = False
    decimales: Optional[int] = None


@dataclass(frozen=True)
class Resultado:
    correctas: int
    incorrectas: int
    blancos: int
    puntaje: Decimal
    alcanza_minimo: bool
    correctas_por_area: Dict[str, int] = field(default_factory=dict)


def _dec(valor, campo: str) -> Decimal:
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Valor numérico inválido en '{campo}': {valor!r}")


def validar_perfil(perfil: dict) -> List[str]:
    """Devuelve la lista de errores de un perfil (vacía si es válido).

    Pensada para la pantalla de edición de perfiles: se llama antes de guardar.
    """
    errores: List[str] = []
    areas = perfil.get("areas") or []
    grupos = perfil.get("grupos") or []
    if not areas:
        errores.append("El perfil debe tener al menos un área.")
    codigos = [a.get("codigo") for a in areas]
    if len(set(codigos)) != len(codigos):
        errores.append("Hay áreas con el mismo código.")
    for a in areas:
        cod = a.get("codigo", "?")
        if int(a.get("nro_preguntas", 0)) <= 0:
            errores.append(f"El área '{cod}' debe tener al menos una pregunta.")
        puntos = a.get("puntos")
        try:
            if isinstance(puntos, dict):
                if not grupos:
                    errores.append(f"El área '{cod}' define puntos por grupo, pero el perfil no tiene grupos.")
                for g in grupos:
                    if g not in puntos and "*" not in puntos:
                        errores.append(f"El área '{cod}' no define puntos para el grupo '{g}'.")
                valores = list(puntos.values())
            else:
                valores = [puntos]
            for v in valores:
                if _dec(v, f"puntos de {cod}") < 0:
                    errores.append(f"El área '{cod}' tiene puntos negativos.")
        except ValueError as e:
            errores.append(str(e))
    pen = perfil.get("penalizacion") or {}
    if pen.get("modo") not in MODOS_PENALIZACION:
        errores.append("El modo de penalización debe ser FIJA o PROPORCIONAL.")
    for campo, valor in (("penalización", pen.get("valor")),
                         ("puntos por pregunta en blanco", perfil.get("puntos_blanco", "0")),
                         ("puntaje mínimo", perfil.get("puntaje_minimo", "0"))):
        try:
            _dec(valor, campo)
        except ValueError as e:
            errores.append(str(e))
    try:
        if pen.get("modo") in MODOS_PENALIZACION and _dec(pen.get("valor"), "penalización") < 0:
            errores.append("La penalización no puede ser negativa.")
    except ValueError:
        pass
    dec = perfil.get("decimales")
    if dec is not None and (not isinstance(dec, int) or dec < 0):
        errores.append("Los decimales de redondeo deben ser un entero mayor o igual a 0.")
    return errores


def reglas_desde_perfil(perfil: dict, grupo: Optional[str] = None) -> Reglas:
    """Convierte un perfil editable en reglas listas para calificar."""
    errores = validar_perfil(perfil)
    if errores:
        raise ValueError("Perfil inválido: " + " | ".join(errores))
    grupos = perfil.get("grupos") or []
    if grupos:
        if grupo is None or grupo.upper() not in [g.upper() for g in grupos]:
            raise ValueError(f"Grupo inválido: {grupo!r}. Opciones: {', '.join(grupos)}")
        grupo = next(g for g in grupos if g.upper() == grupo.upper())

    puntos_area: Dict[str, Decimal] = {}
    for a in perfil["areas"]:
        p = a["puntos"]
        if isinstance(p, dict):
            p = p[grupo] if grupo in p else p["*"]
        puntos_area[a["codigo"]] = _dec(p, f"puntos de {a['codigo']}")

    nombre = perfil["nombre"] + (f", grupo {grupo}" if grupo else "")
    return Reglas(
        nombre=nombre,
        version=int(perfil.get("version", 1)),
        puntos_por_area=puntos_area,
        penalizacion_modo=perfil["penalizacion"]["modo"],
        penalizacion_valor=_dec(perfil["penalizacion"]["valor"], "penalización"),
        puntos_blanco=_dec(perfil.get("puntos_blanco", "0"), "puntos en blanco"),
        puntaje_minimo=_dec(perfil.get("puntaje_minimo", "0"), "puntaje mínimo"),
        truncar_en_cero=bool(perfil.get("truncar_en_cero", False)),
        decimales=perfil.get("decimales"),
    )


def puntaje_maximo(perfil: dict, grupo: Optional[str] = None) -> Decimal:
    """Puntaje máximo teórico (todas correctas). Útil para mostrar en la pantalla del perfil."""
    reglas = reglas_desde_perfil(perfil, grupo)
    return sum((Decimal(a["nro_preguntas"]) * reglas.puntos_por_area[a["codigo"]]
                for a in perfil["areas"]), Decimal("0"))


def calificar(respuestas: Iterable[Respuesta], reglas: Reglas) -> Resultado:
    """Califica un examen con las reglas dadas."""
    correctas = incorrectas = blancos = 0
    por_area: Dict[str, int] = {}
    puntaje = Decimal("0")

    for r in respuestas:
        if r.area not in reglas.puntos_por_area:
            raise ValueError(f"El perfil '{reglas.nombre}' no define puntaje para el área '{r.area}'")
        valor = reglas.puntos_por_area[r.area]
        if r.marcada is None:
            blancos += 1
            puntaje += reglas.puntos_blanco
        elif r.marcada == r.correcta:
            correctas += 1
            por_area[r.area] = por_area.get(r.area, 0) + 1
            puntaje += valor
        else:
            incorrectas += 1
            if reglas.penalizacion_modo == "PROPORCIONAL":
                puntaje -= valor * reglas.penalizacion_valor
            else:
                puntaje -= reglas.penalizacion_valor

    if reglas.truncar_en_cero and puntaje < 0:
        puntaje = Decimal("0")
    if reglas.decimales is not None:
        puntaje = puntaje.quantize(Decimal(1).scaleb(-reglas.decimales), rounding=ROUND_HALF_UP)

    return Resultado(
        correctas=correctas,
        incorrectas=incorrectas,
        blancos=blancos,
        puntaje=puntaje,
        alcanza_minimo=puntaje >= reglas.puntaje_minimo,
        correctas_por_area=por_area,
    )
