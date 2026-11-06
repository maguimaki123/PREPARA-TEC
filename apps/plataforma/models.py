from django.core.exceptions import PermissionDenied
from django.db import models


class ConsumoDNI(models.Model):
    """Consultas a la API de DNI por institución y mes (control de costos)."""
    institucion = models.ForeignKey("instituciones.Institucion", on_delete=models.CASCADE, related_name="consumos_dni")
    mes = models.DateField(help_text="Primer día del mes")
    consultas = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["institucion", "mes"], name="un_consumo_por_mes")]


class AuditoriaAcceso(models.Model):
    """Registro de acciones del administrador de plataforma y accesos de soporte.
    No se puede modificar ni borrar desde la aplicación (RNF-24)."""
    usuario = models.ForeignKey("instituciones.Usuario", on_delete=models.PROTECT, related_name="auditorias")
    institucion = models.ForeignKey("instituciones.Institucion", null=True, blank=True,
                                    on_delete=models.PROTECT, related_name="auditorias")
    accion = models.CharField(max_length=80)
    detalle = models.TextField(blank=True)
    ocurrio_en = models.DateTimeField(auto_now_add=True)
    autorizado_por = models.ForeignKey("instituciones.Usuario", null=True, blank=True,
                                       on_delete=models.PROTECT, related_name="+")

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionDenied("Los registros de auditoría no se pueden modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Los registros de auditoría no se pueden borrar.")
