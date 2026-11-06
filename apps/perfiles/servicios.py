from decimal import Decimal

from django.db import transaction

from apps.banco.models import Area

from .models import Carrera, GrupoCarrera, PerfilArea, PerfilPuntaje, PerfilUniversidad


@transaction.atomic
def crear_desde_definicion(d: dict, institucion=None, creado_por=None) -> PerfilUniversidad:
    """Crea un perfil en la base de datos a partir de su definición (diccionario o JSON).

    Sirve para cargar las plantillas iniciales y, más adelante, para guardar lo
    que el super administrador edite en la pantalla de perfiles."""
    perfil = PerfilUniversidad.objects.create(
        institucion=institucion, nombre=d["nombre"], version=d.get("version", 1),
        penalizacion_modo=d["penalizacion"]["modo"], penalizacion_valor=Decimal(d["penalizacion"]["valor"]),
        puntos_blanco=Decimal(d.get("puntos_blanco", "0")), puntaje_minimo=Decimal(d.get("puntaje_minimo", "0")),
        truncar_en_cero=d.get("truncar_en_cero", False), decimales=d.get("decimales"),
        creado_por=creado_por)
    grupos = {g: GrupoCarrera.objects.create(perfil=perfil, codigo=g) for g in d.get("grupos", [])}
    for g, lista in (d.get("carreras") or {}).items():
        for nombre in lista:
            Carrera.objects.create(grupo=grupos[g], nombre=nombre)
    for orden, a in enumerate(d["areas"]):
        area, _ = Area.objects.get_or_create(institucion=institucion, codigo=a["codigo"],
                                             defaults={"nombre": a.get("nombre", a["codigo"])})
        pa = PerfilArea.objects.create(perfil=perfil, area=area, nro_preguntas=a["nro_preguntas"], orden=orden)
        if isinstance(a["puntos"], dict):
            for g, v in a["puntos"].items():
                PerfilPuntaje.objects.create(perfil_area=pa, grupo=grupos[g], puntos_correcta=Decimal(v))
        else:
            PerfilPuntaje.objects.create(perfil_area=pa, grupo=None, puntos_correcta=Decimal(a["puntos"]))
    return perfil
