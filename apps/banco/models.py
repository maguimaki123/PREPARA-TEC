from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q

from apps.instituciones.querysets import InstitucionalQuerySet


class Area(models.Model):
    """Área de conocimiento. institucion nulo = área global (usada por plantillas)."""
    institucion = models.ForeignKey("instituciones.Institucion", null=True, blank=True,
                                    on_delete=models.CASCADE, related_name="areas")
    codigo = models.CharField(max_length=40, help_text="Identificador que usa el motor de calificación")
    nombre = models.CharField(max_length=150)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["institucion", "codigo"], name="area_codigo_unico")]

    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    class Dificultad(models.TextChoices):
        FACIL = "FACIL", "Fácil"
        MEDIA = "MEDIA", "Media"
        DIFICIL = "DIFICIL", "Difícil"

    institucion = models.ForeignKey("instituciones.Institucion", on_delete=models.CASCADE, related_name="preguntas")
    docente = models.ForeignKey("instituciones.Usuario", on_delete=models.PROTECT, related_name="preguntas")
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="preguntas")
    tema = models.CharField(max_length=150, blank=True)
    dificultad = models.CharField(max_length=8, choices=Dificultad.choices, default=Dificultad.MEDIA)
    enunciado = models.TextField()
    imagen_png = models.FileField(upload_to="preguntas/", null=True, blank=True,
                                  validators=[FileExtensionValidator(["png"])])
    # Una pregunta usada en un examen no se sobrescribe: se crea una versión nueva.
    version = models.PositiveIntegerField(default=1)
    pregunta_anterior = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                          related_name="versiones_nuevas")
    activa = models.BooleanField(default=True)

    objects = InstitucionalQuerySet.as_manager()


class Alternativa(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name="alternativas")
    letra = models.CharField(max_length=1)
    texto = models.TextField()
    es_correcta = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["pregunta", "letra"], name="letra_unica_por_pregunta"),
            models.UniqueConstraint(fields=["pregunta"], condition=Q(es_correcta=True),
                                    name="una_correcta_por_pregunta"),
        ]
