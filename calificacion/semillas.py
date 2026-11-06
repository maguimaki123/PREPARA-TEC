"""Plantillas iniciales (UNAB y UNJFSC).

Son solo datos de partida: la aplicación las carga a la base de datos como
perfiles que el super administrador puede copiar y editar. NO son reglas fijas.
Verificar cada valor con el reglamento vigente de la convocatoria.
"""
import json
from pathlib import Path

_DIR = Path(__file__).parent / "semillas"


def cargar_semilla(nombre: str) -> dict:
    with open(_DIR / f"{nombre}.json", encoding="utf-8") as f:
        return json.load(f)
