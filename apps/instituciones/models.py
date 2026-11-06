from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

ELABORAR_EXAMENES = "ELABORAR_EXAMENES"


class Institucion(models.Model):
    class Tipo(models.TextChoices):
        ACADEMIA = "ACADEMIA", "Academia"
        CIRCULO = "CIRCULO", "Círculo de estudios"
        OTRO = "OTRO", "Otro"

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        SUSPENDIDA = "SUSPENDIDA", "Suspendida"

    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.ACADEMIA)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVA)
    # Límites de uso (nulo = sin límite). Dependen del modelo de cobro: por confirmar.
    limite_docentes = models.PositiveIntegerField(null=True, blank=True)
    limite_examenes_activos = models.PositiveIntegerField(null=True, blank=True)
    limite_consultas_dni_mes = models.PositiveIntegerField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "instituciones"

    def __str__(self):
        return self.nombre

    @property
    def activa(self):
        return self.estado == self.Estado.ACTIVA


class Permiso(models.Model):
    """Permisos asignables a docentes (por ejemplo, ELABORAR_EXAMENES)."""
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=120)

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """Administrador de plataforma, super administradores y docentes.
    Los estudiantes no tienen cuenta. `is_active` hace de "habilitado"."""

    class Rol(models.TextChoices):
        ADMIN_PLATAFORMA = "ADMIN_PLATAFORMA", "Administrador de plataforma"
        SUPER_ADMIN = "SUPER_ADMIN", "Super administrador de institución"
        DOCENTE = "DOCENTE", "Docente"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.DOCENTE)
    institucion = models.ForeignKey(Institucion, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="usuarios")
    permisos = models.ManyToManyField(Permiso, blank=True, related_name="usuarios")

    def _validar_rol(self):
        if self.rol == self.Rol.ADMIN_PLATAFORMA and self.institucion_id is not None:
            raise ValidationError("El administrador de plataforma no pertenece a ninguna institución.")
        if self.rol != self.Rol.ADMIN_PLATAFORMA and self.institucion_id is None:
            raise ValidationError("Los super administradores y docentes deben pertenecer a una institución.")

    def clean(self):
        super().clean()
        self._validar_rol()

    def save(self, *args, **kwargs):
        self._validar_rol()
        super().save(*args, **kwargs)

    @property
    def puede_elaborar_examenes(self):
        """Super administrador, o docente con el permiso ELABORAR_EXAMENES."""
        if self.rol == self.Rol.SUPER_ADMIN:
            return True
        if self.rol == self.Rol.DOCENTE and self.pk:
            return self.permisos.filter(codigo=ELABORAR_EXAMENES).exists()
        return False
