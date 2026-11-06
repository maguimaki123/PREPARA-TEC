# Sistema de Simulacros de Examen de Admisión

Plataforma web multi-institución para que academias preuniversitarias y grupos de estudio creen, apliquen en línea y califiquen automáticamente simulacros de admisión (perfiles UNAB y UNJFSC).

- Documento de software: [`docs/Documento_Software_Simulacros_Admision.docx`](docs/Documento_Software_Simulacros_Admision.docx)
- Plan de tareas: [`docs/TAREAS.md`](docs/TAREAS.md)

## Estado

| Paso | Entregable | Estado |
|---|---|---|
| 1 | Motor de calificación con pruebas (reglas editables, 30 pruebas) | Hecho |
| 2 | Modelo de datos y migraciones (7 apps Django, 21 pruebas) | Hecho; probado con SQLite, falta probar en PostgreSQL |
| 3 | Instituciones, usuarios y permisos | Parcial: modelos, roles y comando del administrador de plataforma; faltan pantallas |
| 4 | Banco de preguntas | Pendiente |
| 5 | Gestión de perfiles desde la interfaz (editor, validación, versiones, simulador) | Parcial: modelos, plantillas, copia y versionado; falta el editor |
| 6 | Crear y publicar examen (URL y QR) | Pendiente |
| 7 | Acceso y rendición del estudiante | Pendiente |
| 8 | Resultados y PDF | Pendiente |
| 9 | Pruebas de carga y seguridad | Pendiente |

## Cómo se definen las reglas de calificación

Las reglas **no están escritas en el código**. Cada universidad es un *perfil* (JSON) con áreas, puntos por área y grupo,
penalización (fija o proporcional), puntos en blanco, puntaje mínimo, truncamiento y redondeo. El super administrador lo
edita desde la interfaz; cada cambio crea una versión nueva y los exámenes ya creados conservan la suya.
`calificacion/semillas/unab.json` y `unjfsc.json` son solo plantillas iniciales. Formato completo en `calificacion/motor.py`.

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Sin variables de entorno usa SQLite (solo desarrollo). Para PostgreSQL, defina POSTGRES_DB, POSTGRES_USER, etc. (ver .env.example)
python manage.py migrate
python manage.py cargar_plantillas            # plantillas globales UNAB y UNJFSC
python manage.py crear_admin_plataforma --usuario TU_USUARIO --correo tu@correo.pe
python manage.py runserver                    # panel provisional en /admin/
```

## Pruebas

```bash
pytest                    # motor de calificación (30 pruebas, sin base de datos)
python manage.py test     # modelos y reglas de negocio (21 pruebas)
```

## Estructura

```
calificacion/   motor de calificación (función pura) y plantillas JSON
apps/instituciones   instituciones, usuarios (3 roles), permisos
apps/plataforma      consumo de DNI y auditoría (no modificable)
apps/banco           áreas, preguntas (versionadas), alternativas
apps/perfiles        perfiles de calificación editables, copia y versiones
apps/examenes        exámenes con copia de reglas al publicar, URL por token
apps/rendicion       intentos, respuestas, incidencias, resultados y calificación
apps/reportes        PDF de resultados almacenados
```

## Flujo de trabajo del equipo

- `main`: versión estable, protegida. `develop`: integración.
- Una rama por tarea: `feature/<nombre>` (por ejemplo `feature/modelo-datos`).
- Se fusiona con pull request revisado por otro integrante.
- Commits con prefijo: `feat:`, `fix:`, `docs:`, `test:`.
- Nunca subir contraseñas ni tokens (usar variables de entorno; `.env` está en `.gitignore`).

## Puntos por confirmar con el reglamento

- UNAB: si un puntaje negativo se trunca en 0 (`truncar_en_cero` en `calificacion/motor.py`).
- UNJFSC: distribución de las 80 preguntas por área (se asumen 20 por área).
- Que alcanzar exactamente el puntaje mínimo cuenta como "alcanza" (se usa mayor o igual).
