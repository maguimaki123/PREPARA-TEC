from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.banco.models import Area, Pregunta
from apps.instituciones.models import ELABORAR_EXAMENES, Institucion, Permiso, Usuario
from apps.plataforma.models import AuditoriaAcceso
from django.core.exceptions import PermissionDenied


class RolesTests(TestCase):
    def setUp(self):
        self.inst = Institucion.objects.create(nombre="Academia A")
        self.otra = Institucion.objects.create(nombre="Academia B")

    def test_admin_plataforma_no_pertenece_a_institucion(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create_user("p", password="x", rol=Usuario.Rol.ADMIN_PLATAFORMA, institucion=self.inst)
        Usuario.objects.create_user("p", password="x", rol=Usuario.Rol.ADMIN_PLATAFORMA)

    def test_docente_y_super_admin_requieren_institucion(self):
        for rol in (Usuario.Rol.DOCENTE, Usuario.Rol.SUPER_ADMIN):
            with self.assertRaises(ValidationError):
                Usuario.objects.create_user(f"u-{rol}", password="x", rol=rol)

    def test_comando_crea_admin_de_plataforma(self):
        call_command("crear_admin_plataforma", usuario="duena", correo="a@b.pe", password="Clave-Segura-123")
        u = Usuario.objects.get(username="duena")
        self.assertEqual(u.rol, Usuario.Rol.ADMIN_PLATAFORMA)
        self.assertIsNone(u.institucion)

    def test_permiso_de_elaborador(self):
        docente = Usuario.objects.create_user("d", password="x", rol=Usuario.Rol.DOCENTE, institucion=self.inst)
        self.assertFalse(docente.puede_elaborar_examenes)
        docente.permisos.add(Permiso.objects.create(codigo=ELABORAR_EXAMENES, nombre="Elaborar exámenes"))
        self.assertTrue(docente.puede_elaborar_examenes)
        sa = Usuario.objects.create_user("s", password="x", rol=Usuario.Rol.SUPER_ADMIN, institucion=self.inst)
        self.assertTrue(sa.puede_elaborar_examenes)

    def test_aislamiento_de_preguntas_por_institucion(self):
        area = Area.objects.create(codigo="X", nombre="X")
        d1 = Usuario.objects.create_user("d1", password="x", institucion=self.inst)
        d2 = Usuario.objects.create_user("d2", password="x", institucion=self.otra)
        Pregunta.objects.create(institucion=self.inst, docente=d1, area=area, enunciado="de A")
        Pregunta.objects.create(institucion=self.otra, docente=d2, area=area, enunciado="de B")
        self.assertEqual([p.enunciado for p in Pregunta.objects.de_institucion(self.inst)], ["de A"])

    def test_auditoria_no_se_modifica_ni_se_borra(self):
        p = Usuario.objects.create_user("p", password="x", rol=Usuario.Rol.ADMIN_PLATAFORMA)
        a = AuditoriaAcceso.objects.create(usuario=p, institucion=self.inst, accion="ACCESO_SOPORTE")
        a.detalle = "cambio"
        with self.assertRaises(PermissionDenied):
            a.save()
        with self.assertRaises(PermissionDenied):
            a.delete()
