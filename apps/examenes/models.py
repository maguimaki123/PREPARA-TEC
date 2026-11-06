import secrets

from django.core.exceptions import ValidationError
from django.db import models

from apps.instituciones.querysets import InstitucionalQuerySet


def _token():
    return secrets.token_urlsafe(16)


class Examen(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PUBLICADO = "PUBLICADO", "Publicado"
        CERRADO = "CERRADO", "Cerrado"

    institucion = models.ForeignKey("instituciones.Institucion", on_delete=models.CASCADE, related_name="examenes")
    creado_por = models.ForeignKey("instituciones.Usuario", on_delete=models.PROTECT, related_name="examenes")
    perfil = models.ForeignKey("perfiles.PerfilUniversidad", on_delete=models.PROTECT, related_name="examenes")
    titulo = models.CharField(max_length=200)
    duracion_min = models.PositiveIntegerField()
    abre_en = models.DateTimeField(null=True, blank=True)
    cierra_en = models.DateTimeField(null=True, blank=True)
    token_publico = models.CharField(max_length=32, unique=True, default=_token)   # base de la URL y del QR
    # Copia de las reglas al publicar: si el perfil cambia después, este examen no se altera.
    reglas_snapshot = models.JSONField(null=True, blank=True)
    max_incidencias = models.PositiveIntegerField(default=0)   # 0 = se detiene al primer evento (propuesta)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    creado_en = models.DateTimeField(auto_now_add=True)

    objects = InstitucionalQuerySet.as_manager()

    def __str__(self):
        return self.titulo

    def clean(self):
        if not self.creado_por.puede_elaborar_examenes:
            raise ValidationError("Este usuario no tiene permiso para crear exámenes.")
        if self.creado_por.institucion_id != self.institucion_id:
            raise ValidationError("El creador no pertenece a la institución del examen.")
        if self.perfil.institucion_id not in (None, self.institucion_id):
            raise ValidationError("El perfil pertenece a otra institución.")
        if not self.institucion.activa:
            raise ValidationError("La institución está suspendida.")

    def publicar(self):
        """Valida, guarda la copia de las reglas y deja el examen publicado."""
        self.clean()
        self.reglas_snapshot = self.perfil.a_dict()
        self.estado = self.Estado.PUBLICADO
        self.save()


class ExamenPregunta(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="preguntas")
    pregunta = models.ForeignKey("banco.Pregunta", on_delete=models.PROTECT)
    orden = models.PositiveIntegerField()

    class Meta:
        ordering = ["orden"]
        constraints = [models.UniqueConstraint(fields=["examen", "pregunta"], name="pregunta_unica_por_examen")]
