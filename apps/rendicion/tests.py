from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.banco.models import Alternativa, Area, Pregunta
from apps.examenes.models import Examen, ExamenPregunta
from apps.instituciones.models import ELABORAR_EXAMENES, Institucion, Permiso, Usuario
from apps.perfiles.models import PerfilUniversidad
from apps.rendicion.models import Intento, Respuesta
from apps.rendicion.servicios import calificar_intento


class RendicionTests(TestCase):
    """Camino completo: plantilla -> perfil de la institución -> examen -> intento -> resultado."""

    def setUp(self):
        call_command("cargar_plantillas", verbosity=0)
        self.inst = Institucion.objects.create(nombre="Academia A")
        self.admin = Usuario.objects.create_user("sa", password="x", rol=Usuario.Rol.SUPER_ADMIN, institucion=self.inst)
        self.docente = Usuario.objects.create_user("d", password="x", rol=Usuario.Rol.DOCENTE, institucion=self.inst)
        self.perfil = PerfilUniversidad.objects.get(institucion=None, nombre="UNAB ordinario").duplicar(self.inst, self.admin)
        area = Area.objects.get(institucion=None, codigo="GENERAL")
        self.preguntas = []
        for i in range(5):
            p = Pregunta.objects.create(institucion=self.inst, docente=self.docente, area=area, enunciado=f"P{i}")
            Alternativa.objects.create(pregunta=p, letra="A", texto="correcta", es_correcta=True)
            Alternativa.objects.create(pregunta=p, letra="B", texto="incorrecta")
            self.preguntas.append(p)
        self.examen = Examen.objects.create(institucion=self.inst, creado_por=self.admin, perfil=self.perfil,
                                            titulo="Simulacro 1", duracion_min=60)
        self.eps = [ExamenPregunta.objects.create(examen=self.examen, pregunta=p, orden=i)
                    for i, p in enumerate(self.preguntas)]
        self.examen.publicar()

    def _intento(self, dni="12345678"):
        ahora = timezone.now()
        return Intento.objects.create(examen=self.examen, dni=dni, nombres="Ana", apellidos="Pérez",
                                      celular="987654321", acepto_datos=True, acepto_en=ahora, inicio_en=ahora,
                                      limite_en=ahora + timedelta(minutes=60), estado=Intento.Estado.EN_CURSO)

    def _marcar(self, intento, letras):
        for ep, letra in zip(self.eps, letras):
            if letra:
                alt = Alternativa.objects.get(pregunta=ep.pregunta, letra=letra)
                Respuesta.objects.create(intento=intento, examen_pregunta=ep, alternativa=alt)

    def test_califica_con_el_motor(self):
        i = self._intento()
        self._marcar(i, ["A", "A", "A", "B", None])      # 3 correctas, 1 incorrecta, 1 en blanco
        r = calificar_intento(i)
        self.assertEqual((r.correctas, r.incorrectas, r.blancos), (3, 1, 1))
        self.assertEqual(r.puntaje, Decimal("59.4375"))   # 3*20 - 0.5625
        self.assertFalse(r.alcanza_minimo)

    def test_examen_interrumpido_cuenta_lo_no_respondido_como_blanco(self):
        i = self._intento()
        self._marcar(i, ["A", "A", None, None, None])
        r = calificar_intento(i)
        self.assertEqual((r.correctas, r.incorrectas, r.blancos, r.puntaje), (2, 0, 3, Decimal("40")))

    def test_cambiar_el_perfil_no_altera_un_examen_publicado(self):
        i = self._intento()
        self._marcar(i, ["A", "A", "A", "B", None])
        self.perfil.penalizacion_valor = Decimal("5")
        self.perfil.save()
        self.assertEqual(calificar_intento(i).puntaje, Decimal("59.4375"))    # usa la copia de reglas
        self.assertEqual(self.examen.reglas_snapshot["penalizacion"]["valor"], "0.5625")

    def test_un_solo_intento_por_dni_y_examen(self):
        self._intento("11111111")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._intento("11111111")

    def test_validacion_de_dni_y_celular(self):
        i = self._intento()
        i.dni = "123"
        with self.assertRaises(ValidationError):
            i.full_clean()
        i.dni, i.celular = "12345678", "123456789"
        with self.assertRaises(ValidationError):
            i.full_clean()

    def test_docente_sin_permiso_no_publica_examenes(self):
        ex = Examen.objects.create(institucion=self.inst, creado_por=self.docente, perfil=self.perfil,
                                   titulo="X", duracion_min=30)
        with self.assertRaises(ValidationError):
            ex.publicar()
        self.docente.permisos.add(Permiso.objects.create(codigo=ELABORAR_EXAMENES, nombre="Elaborar"))
        ex.publicar()
        self.assertEqual(ex.estado, Examen.Estado.PUBLICADO)

    def test_institucion_suspendida_no_publica(self):
        self.inst.estado = Institucion.Estado.SUSPENDIDA
        self.inst.save()
        ex = Examen.objects.create(institucion=self.inst, creado_por=self.admin, perfil=self.perfil,
                                   titulo="Y", duracion_min=30)
        with self.assertRaises(ValidationError):
            ex.publicar()

    def test_perfil_de_otra_institucion_no_se_puede_usar(self):
        otra = Institucion.objects.create(nombre="Academia B")
        perfil_b = PerfilUniversidad.objects.get(institucion=None, nombre="UNAB ordinario").duplicar(otra)
        ex = Examen.objects.create(institucion=self.inst, creado_por=self.admin, perfil=perfil_b,
                                   titulo="Z", duracion_min=30)
        with self.assertRaises(ValidationError):
            ex.publicar()
