import copy
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from apps.instituciones.models import Institucion, Usuario
from apps.perfiles.models import PerfilUniversidad
from calificacion import cargar_semilla, reglas_desde_perfil, validar_perfil


class PerfilesTests(TestCase):
    def setUp(self):
        call_command("cargar_plantillas", verbosity=0)
        self.unab = PerfilUniversidad.objects.get(institucion=None, nombre="UNAB ordinario")
        self.unj = PerfilUniversidad.objects.get(institucion=None, nombre="UNJFSC ordinario")

    def test_carga_es_idempotente(self):
        call_command("cargar_plantillas", verbosity=0)
        self.assertEqual(PerfilUniversidad.objects.filter(institucion=None).count(), 2)

    def test_perfil_de_la_base_equivale_al_json_para_el_motor(self):
        self.assertEqual(reglas_desde_perfil(self.unab.a_dict()), reglas_desde_perfil(cargar_semilla("unab")))
        for g in "ABCD":
            self.assertEqual(reglas_desde_perfil(self.unj.a_dict(), g),
                             reglas_desde_perfil(cargar_semilla("unjfsc"), g))

    def test_perfiles_cargados_son_validos(self):
        self.assertEqual(validar_perfil(self.unab.a_dict()), [])
        self.assertEqual(validar_perfil(self.unj.a_dict()), [])

    def test_carreras_cargadas_por_grupo(self):
        grupo_a = self.unj.grupos.get(codigo="A")
        self.assertTrue(grupo_a.carreras.filter(nombre="Ingeniería de Sistemas").exists())
        self.assertTrue(self.unj.grupos.get(codigo="B").carreras.filter(nombre="Medicina Humana").exists())

    def test_duplicar_plantilla_para_una_institucion_no_toca_la_global(self):
        inst = Institucion.objects.create(nombre="Academia A")
        admin = Usuario.objects.create_user("sa", password="x", rol=Usuario.Rol.SUPER_ADMIN, institucion=inst)
        copia = self.unab.duplicar(inst, admin)
        copia.penalizacion_valor = Decimal("1")
        copia.save()
        self.assertEqual(copia.institucion, inst)
        self.assertEqual(self.unab.a_dict()["penalizacion"]["valor"], "0.5625")   # la global sigue igual
        self.assertEqual(copia.a_dict()["penalizacion"]["valor"], "1")

    def test_nueva_version_conserva_la_anterior(self):
        v2 = self.unab.nueva_version()
        v2.puntaje_minimo = Decimal("550")
        v2.save()
        self.assertEqual((v2.version, v2.version_anterior), (2, self.unab))
        self.assertEqual(self.unab.a_dict()["puntaje_minimo"], "500")
        self.assertEqual(v2.a_dict()["puntaje_minimo"], "550")
        self.assertEqual(len(v2.a_dict()["areas"]), len(self.unab.a_dict()["areas"]))

    def test_unjfsc_copiado_conserva_grupos_y_puntos(self):
        copia = self.unj.duplicar(None)  # copia dentro de las plantillas, solo para comprobar la clonación
        self.assertEqual(copia.a_dict()["areas"], self.unj.a_dict()["areas"])
