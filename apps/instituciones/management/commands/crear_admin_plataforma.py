import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.instituciones.models import Usuario


class Command(BaseCommand):
    help = ("Crea la cuenta de administrador de plataforma. Solo se puede hacer desde la "
            "línea de comandos del servidor, nunca desde la interfaz pública (RNF-23).")

    def add_arguments(self, parser):
        parser.add_argument("--usuario", required=True)
        parser.add_argument("--correo", required=True)
        parser.add_argument("--password", help="Si se omite, se pide por teclado.")

    def handle(self, *args, **o):
        if Usuario.objects.filter(username=o["usuario"]).exists():
            raise CommandError("Ya existe un usuario con ese nombre.")
        password = o["password"] or getpass.getpass("Contraseña: ")
        if not password:
            raise CommandError("La contraseña no puede estar vacía.")
        Usuario.objects.create_user(username=o["usuario"], email=o["correo"], password=password,
                                    rol=Usuario.Rol.ADMIN_PLATAFORMA, institucion=None)
        self.stdout.write(self.style.SUCCESS("Administrador de plataforma creado."))
