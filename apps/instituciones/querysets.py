from django.db import models


class InstitucionalQuerySet(models.QuerySet):
    """Filtro por institución. Toda consulta de datos propios de una institución
    debe pasar por `de_institucion` (aislamiento entre instituciones, RNF-12)."""

    def de_institucion(self, institucion):
        return self.filter(institucion=institucion)
