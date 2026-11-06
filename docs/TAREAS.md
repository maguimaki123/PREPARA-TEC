# Plan de tareas (para crear como Issues en GitHub)

Etiquetas sugeridas: `prioridad:alta`, `prioridad:media`, `backend`, `frontend`, `docs`, `pruebas`.
Hitos sugeridos: uno por paso del orden de construcción.

## Hito 1: Motor de calificación
- [x] Función `calificar` con aritmética Decimal
- [x] Reglas leídas de un perfil editable (`reglas_desde_perfil`), no fijas en el código
- [x] Validación de perfiles (`validar_perfil`) y puntaje máximo
- [x] Plantillas UNAB y UNJFSC en JSON
- [x] Pruebas UNAB-01..07, UNJ-01..06, EDIT-01..07 y VAL-01..03
- [ ] Confirmar con el reglamento: puntaje negativo, distribución UNJFSC, borde del mínimo

## Hito 2: Modelo de datos
- [x] Framework y base de datos elegidos: Django y PostgreSQL (SQLite solo en desarrollo)
- [x] Entidades de la sección 6.2 con migraciones
- [x] Filtro por institución (`de_institucion`) en preguntas y exámenes
- [ ] Probar las migraciones en PostgreSQL
- [ ] Aplicar el filtro por institución en todas las vistas que se creen

## Hito 3: Instituciones, usuarios y permisos
- [ ] HU-01 Habilitar y deshabilitar docentes (prioridad alta)
- [ ] HU-02 Asignar permiso de elaborador de exámenes (prioridad alta)
- [ ] Inicio de sesión y verificación de rol, permiso e institución
- [x] Rol ADMIN_PLATAFORMA (sin institución), creado solo por línea de comandos
- [ ] Verificación en dos pasos para el administrador de plataforma
- [ ] HU-13 Crear institución y su primer super administrador (prioridad alta)
- [ ] HU-14 Suspender y reactivar instituciones (prioridad media)
- [ ] HU-17 Acceso de soporte con autorización del super administrador y registro de auditoría (prioridad media)
- [x] Tabla de auditoría de accesos (AuditoriaAcceso), no modificable ni borrable
- [ ] Pantallas de instituciones, docentes y permisos

## Hito 4: Banco de preguntas
- [ ] HU-03 Cargar preguntas con texto y PNG (prioridad alta)
- [ ] Versionado de preguntas usadas en exámenes

## Hito 5: Perfiles de calificación editables (RF-03)
- [x] Cargar las plantillas UNAB y UNJFSC a la base de datos (`cargar_plantillas`)
- [x] Copiar una plantilla para una institución y crear versiones (modelo)
- [ ] Pantalla A4: editor de áreas, puntos por área y grupo, penalización, puntos en blanco, mínimo, redondeo
- [ ] Validación al guardar (usar `validar_perfil`)
- [ ] Versionado e historial de cambios
- [ ] Simulador de puntaje y puntaje máximo en la pantalla
- [ ] Recalificar exámenes con una nueva versión (con confirmación)
- [ ] HU-15 Plantillas globales mantenidas por el administrador de plataforma, que las instituciones copian (prioridad alta)

## Hito 6: Exámenes
- [ ] HU-04 Crear examen según perfil (prioridad alta)
- [ ] HU-05 Publicar con URL y código QR (prioridad alta)

## Hito 7: Rendición del estudiante
- [ ] HU-06 Ingreso con DNI y celular, consulta a la API (prioridad alta)
- [ ] HU-07 Cronómetro y guardado automático (prioridad alta)
- [ ] HU-08 Detección de salida de la ventana (prioridad alta)
- [ ] HU-09 Confirmación de envío (prioridad alta)
- [ ] HU-10 Puntaje final y motivo de finalización (prioridad alta)
- [ ] Cierre automático por el servidor al vencer la hora límite

## Hito 8: Resultados
- [ ] HU-11 PDF de resultados almacenado (prioridad alta)
- [ ] HU-12 Celular de contacto visible solo a administradores (prioridad media)

## Hito 8b: Límites de uso (depende del modelo de cobro)
- [ ] HU-16 Límite y consumo mensual de consultas de DNI por institución (prioridad media)
- [ ] Límites de docentes y exámenes activos por institución (por confirmar)

## Hito 9: Pruebas y cierre
- [ ] Pruebas de seguridad SEG-01..09
- [ ] Prueba de carga CAR-01
- [ ] Manuales de usuario y técnico
