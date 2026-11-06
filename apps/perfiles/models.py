"""Perfiles de calificación editables desde la interfaz (RF-03).

Las reglas viven en la base de datos, no en el código. `a_dict()` las entrega
en el formato que entiende el motor (`calificacion.reglas_desde_perfil`).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from calificacion import validar_perfil


def _s(valor: Decimal) -> str:
    """Decimal a texto sin ceros sobrantes: 20.0000 -> '20', 0.5625 -> '0.5625'."""
    return format(Decimal(valor).normalize(), "f")


class PerfilUniversidad(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        VIGENTE = "VIGENTE", "Vigente"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    class ModoPenalizacion(models.TextChoices):
        FIJA = "FIJA", "Fija"
        PROPORCIONAL = "PROPORCIONAL", "Proporcional"

    # institucion nulo = plantilla global (solo la edita el administrador de plataforma)
    institucion = models.ForeignKey("instituciones.Institucion", null=True, blank=True,
                                    on_delete=models.CASCADE, related_name="perfiles")
    nombre = models.CharField(max_length=150)
    version = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    penalizacion_modo = models.CharField(max_length=13, choices=ModoPenalizacion.choices, default=ModoPenalizacion.FIJA)
    penalizacion_valor = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    puntos_blanco = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    puntaje_minimo = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    truncar_en_cero = models.BooleanField(default=False)
    decimales = models.PositiveSmallIntegerField(null=True, blank=True)
    # Auditoría: quién lo creó y de qué versión viene
    creado_por = models.ForeignKey("instituciones.Usuario", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+")
    creado_en = models.DateTimeField(auto_now_add=True)
    version_anterior = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="versiones_nuevas")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["institucion", "nombre", "version"], name="perfil_version_unica")]

    def __str__(self):
        return f"{self.nombre} v{self.version}"

    # ----- conversión hacia el motor -----
    def a_dict(self) -> dict:
        grupos = list(self.grupos.order_by("id"))
        areas = []
        for pa in self.areas_perfil.select_related("area").order_by("orden", "id"):
            por_grupo = {p.grupo_id: p.puntos_correcta for p in pa.puntajes.all()}
            if grupos:
                puntos = {g.codigo: _s(por_grupo[g.id]) for g in grupos if g.id in por_grupo}
            else:
                puntos = _s(por_grupo[None]) if None in por_grupo else None
            areas.append({"codigo": pa.area.codigo, "nombre": pa.area.nombre,
                          "nro_preguntas": pa.nro_preguntas, "puntos": puntos})
        return {
            "nombre": self.nombre,
            "version": self.version,
            "areas": areas,
            "grupos": [g.codigo for g in grupos],
            "penalizacion": {"modo": self.penalizacion_modo, "valor": _s(self.penalizacion_valor)},
            "puntos_blanco": _s(self.puntos_blanco),
            "puntaje_minimo": _s(self.puntaje_minimo),
            "truncar_en_cero": self.truncar_en_cero,
            "decimales": self.decimales,
        }

    def clean(self):
        errores = validar_perfil(self.a_dict()) if self.pk else []
        if errores:
            raise ValidationError(errores)

    # ----- copia y versionado (RF-03.3 y RF-03.5) -----
    def _copiar(self, institucion, version, anterior, creado_por):
        nuevo = PerfilUniversidad.objects.create(
            institucion=institucion, nombre=self.nombre, version=version, estado=self.Estado.BORRADOR,
            penalizacion_modo=self.penalizacion_modo, penalizacion_valor=self.penalizacion_valor,
            puntos_blanco=self.puntos_blanco, puntaje_minimo=self.puntaje_minimo,
            truncar_en_cero=self.truncar_en_cero, decimales=self.decimales,
            creado_por=creado_por, version_anterior=anterior)
        mapa_grupos = {}
        for g in self.grupos.order_by("id"):
            ng = GrupoCarrera.objects.create(perfil=nuevo, codigo=g.codigo)
            mapa_grupos[g.id] = ng
            for c in g.carreras.all():
                Carrera.objects.create(grupo=ng, nombre=c.nombre)
        for pa in self.areas_perfil.order_by("orden", "id"):
            npa = PerfilArea.objects.create(perfil=nuevo, area=pa.area, nro_preguntas=pa.nro_preguntas, orden=pa.orden)
            for p in pa.puntajes.all():
                PerfilPuntaje.objects.create(perfil_area=npa, puntos_correcta=p.puntos_correcta,
                                             grupo=mapa_grupos.get(p.grupo_id))
        return nuevo

    def duplicar(self, institucion, creado_por=None):
        """Copia una plantilla (o un perfil) para que una institución la edite."""
        return self._copiar(institucion, 1, None, creado_por)

    def nueva_version(self, creado_por=None):
        """Crea la versión siguiente para editarla; esta versión queda intacta."""
        return self._copiar(self.institucion, self.version + 1, self, creado_por)


class PerfilArea(models.Model):
    perfil = models.ForeignKey(PerfilUniversidad, on_delete=models.CASCADE, related_name="areas_perfil")
    area = models.ForeignKey("banco.Area", on_delete=models.PROTECT)
    nro_preguntas = models.PositiveIntegerField()
    orden = models.PositiveIntegerField(default=0)


class GrupoCarrera(models.Model):
    perfil = models.ForeignKey(PerfilUniversidad, on_delete=models.CASCADE, related_name="grupos")
    codigo = models.CharField(max_length=10)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["perfil", "codigo"], name="grupo_unico_por_perfil")]


class Carrera(models.Model):
    grupo = models.ForeignKey(GrupoCarrera, on_delete=models.CASCADE, related_name="carreras")
    nombre = models.CharField(max_length=150)


class PerfilPuntaje(models.Model):
    """Puntos por respuesta correcta de un área; grupo nulo si el perfil no usa grupos."""
    perfil_area = models.ForeignKey(PerfilArea, on_delete=models.CASCADE, related_name="puntajes")
    grupo = models.ForeignKey(GrupoCarrera, null=True, blank=True, on_delete=models.CASCADE)
    puntos_correcta = models.DecimalField(max_digits=10, decimal_places=4)
