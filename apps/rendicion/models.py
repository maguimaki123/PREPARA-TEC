from django.core.validators import RegexValidator
from django.db import models


class Intento(models.Model):
    class Estado(models.TextChoices):
        INICIADO = "INICIADO", "Iniciado"
        EN_CURSO = "EN_CURSO", "En curso"
        FINALIZADO = "FINALIZADO", "Finalizado"

    class Motivo(models.TextChoices):
        ENVIADO = "ENVIADO", "Enviado"
        TIEMPO_AGOTADO = "TIEMPO_AGOTADO", "Tiempo agotado"
        INTERRUMPIDO = "INTERRUMPIDO", "Interrumpido"

    examen = models.ForeignKey("examenes.Examen", on_delete=models.CASCADE, related_name="intentos")
    dni = models.CharField(max_length=8, validators=[RegexValidator(r"^\d{8}$", "El DNI debe tener 8 dígitos.")])
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    nombres_verificados = models.BooleanField(default=False)   # falso si se ingresaron a mano
    celular = models.CharField(max_length=9, validators=[RegexValidator(r"^9\d{8}$", "El celular debe tener 9 dígitos y empezar con 9.")])
    carrera = models.ForeignKey("perfiles.Carrera", null=True, blank=True, on_delete=models.PROTECT)
    grupo = models.CharField(max_length=10, blank=True)         # grupo deducido de la carrera
    acepto_datos = models.BooleanField(default=False)
    acepto_en = models.DateTimeField(null=True, blank=True)
    inicio_en = models.DateTimeField(null=True, blank=True)
    limite_en = models.DateTimeField(null=True, blank=True)     # lo calcula el servidor
    fin_en = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.INICIADO)
    motivo_fin = models.CharField(max_length=15, choices=Motivo.choices, blank=True)
    sesion = models.CharField(max_length=64, blank=True)        # identificador de sesión del navegador

    class Meta:
        constraints = [models.UniqueConstraint(fields=["examen", "dni"], name="un_intento_por_dni")]   # por confirmar


class Respuesta(models.Model):
    intento = models.ForeignKey(Intento, on_delete=models.CASCADE, related_name="respuestas")
    examen_pregunta = models.ForeignKey("examenes.ExamenPregunta", on_delete=models.PROTECT)
    alternativa = models.ForeignKey("banco.Alternativa", on_delete=models.PROTECT)
    marcada_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["intento", "examen_pregunta"], name="una_respuesta_por_pregunta")]


class Incidencia(models.Model):
    class Tipo(models.TextChoices):
        CAMBIO_PESTANA = "CAMBIO_PESTANA", "Cambio de pestaña"
        CAMBIO_VENTANA = "CAMBIO_VENTANA", "Cambio de ventana"
        SALIDA_APP = "SALIDA_APP", "Salida de la aplicación"
        OTRO = "OTRO", "Otro"

    intento = models.ForeignKey(Intento, on_delete=models.CASCADE, related_name="incidencias")
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    ocurrio_en = models.DateTimeField(auto_now_add=True)


class Resultado(models.Model):
    intento = models.OneToOneField(Intento, on_delete=models.CASCADE, related_name="resultado")
    correctas = models.PositiveIntegerField()
    incorrectas = models.PositiveIntegerField()
    blancos = models.PositiveIntegerField()
    puntaje = models.DecimalField(max_digits=12, decimal_places=4)   # decimal exacto (RNF-01)
    alcanza_minimo = models.BooleanField()
    posicion = models.PositiveIntegerField(null=True, blank=True)
    version_reglas = models.PositiveIntegerField()
