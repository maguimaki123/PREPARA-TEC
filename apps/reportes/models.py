from django.db import models


class ReportePDF(models.Model):
    """PDF de resultados de un examen. Queda almacenado (RF-08.3)."""
    examen = models.ForeignKey("examenes.Examen", on_delete=models.CASCADE, related_name="reportes")
    generado_por = models.ForeignKey("instituciones.Usuario", on_delete=models.PROTECT, related_name="+")
    generado_en = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to="reportes/")
    hash = models.CharField(max_length=64)   # SHA-256 del archivo
