"""Une la base de datos con el motor de calificación."""
from apps.rendicion.models import Resultado
from calificacion import Respuesta, calificar, reglas_desde_perfil


def calificar_intento(intento) -> Resultado:
    """Califica un intento con las reglas guardadas en el examen (reglas_snapshot).

    Las preguntas sin respuesta registrada cuentan como en blanco, de modo que
    sirve igual para un envío normal, un fin de tiempo o un examen interrumpido."""
    examen = intento.examen
    reglas = reglas_desde_perfil(examen.reglas_snapshot, intento.grupo or None)
    marcadas = {r.examen_pregunta_id: r.alternativa
                for r in intento.respuestas.select_related("alternativa")}
    respuestas = []
    for ep in examen.preguntas.select_related("pregunta__area").prefetch_related("pregunta__alternativas"):
        correcta = next(a.letra for a in ep.pregunta.alternativas.all() if a.es_correcta)
        alt = marcadas.get(ep.id)
        respuestas.append(Respuesta(area=ep.pregunta.area.codigo, correcta=correcta,
                                    marcada=alt.letra if alt else None))
    res = calificar(respuestas, reglas)
    resultado, _ = Resultado.objects.update_or_create(
        intento=intento,
        defaults=dict(correctas=res.correctas, incorrectas=res.incorrectas, blancos=res.blancos,
                      puntaje=res.puntaje, alcanza_minimo=res.alcanza_minimo,
                      version_reglas=reglas.version))
    return resultado
