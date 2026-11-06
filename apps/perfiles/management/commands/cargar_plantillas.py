from django.core.management.base import BaseCommand

from apps.perfiles.models import PerfilUniversidad
from apps.perfiles.servicios import crear_desde_definicion
from calificacion import cargar_semilla


class Command(BaseCommand):
    help = "Carga las plantillas globales iniciales (UNAB y UNJFSC). Es seguro ejecutarlo varias veces."

    def handle(self, *args, **opciones):
        hablar = opciones.get("verbosity", 1) > 0
        for nombre in ("unab", "unjfsc"):
            d = cargar_semilla(nombre)
            if PerfilUniversidad.objects.filter(institucion=None, nombre=d["nombre"], version=d["version"]).exists():
                hablar and self.stdout.write(f"Ya existe: {d['nombre']} v{d['version']}")
                continue
            perfil = crear_desde_definicion(d, institucion=None)
            perfil.estado = PerfilUniversidad.Estado.VIGENTE
            perfil.save(update_fields=["estado"])
            hablar and self.stdout.write(self.style.SUCCESS(f"Plantilla cargada: {perfil}"))
        hablar and self.stdout.write("Recuerde verificar los valores con el reglamento vigente de cada convocatoria.")
