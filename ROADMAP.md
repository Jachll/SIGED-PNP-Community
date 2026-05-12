# Roadmap

## Stabilization / Hardening

Estado: in progress

Objetivo: consolidar una base estable para colaboración pública.

Tareas:

- Mantener CI verde.
- Fortalecer validaciones de configuración.
- Revisar errores y mensajes operativos.
- Aumentar cobertura de pruebas críticas.

Riesgos: entornos locales heterogéneos, dependencias de PostGIS y diferencias Windows/Linux.

## Open Source Readiness

Estado: in progress

Objetivo: mejorar señales públicas de mantenimiento y seguridad.

Tareas:

- Mantener licencia, guías y templates.
- Publicar solo datos sintéticos.
- Documentar límites de la edición pública.
- Crear releases alfa revisables.

Riesgos: inclusión accidental de datos o activos de origen incierto.

## Dashboard Operacional

Estado: planned

Objetivo: mejorar lectura operativa del mapa, filtros y paneles.

Tareas:

- Refinar estados vacíos y de carga.
- Mejorar accesibilidad.
- Añadir capturas con datos sintéticos.

Riesgos: romper el flujo territorial o degradar rendimiento de mapa.

## Indicadores Operacionales

Estado: planned

Objetivo: ampliar métricas para priorización territorial.

Tareas:

- Definir indicadores base.
- Agregar pruebas de agregación.
- Documentar interpretación y límites.

Riesgos: indicadores mal interpretados si los datos fuente no están normalizados.

## Libro Operacional

Estado: planned

Objetivo: preparar una vista ordenada para seguimiento operativo.

Tareas:

- Diseñar modelo de eventos operativos.
- Definir permisos por rol.
- Preparar exportación o consulta auditada.

Riesgos: exposición de información sensible en implementaciones reales.

## Reportes PDF/Excel

Estado: planned

Objetivo: habilitar reportes reproducibles con datos autorizados.

Tareas:

- Definir plantillas.
- Incluir metadatos de filtros.
- Añadir pruebas de generación.

Riesgos: exportar información real sin controles de anonimización.

## Dockerización

Estado: planned

Objetivo: simplificar arranque local y CI extendido.

Tareas:

- Crear Dockerfile backend.
- Crear contenedor frontend.
- Agregar compose local con PostGIS.

Riesgos: aumentar complejidad de configuración inicial.

## Migraciones Controladas

Estado: planned

Objetivo: formalizar cambios de base de datos.

Tareas:

- Evaluar herramienta de migraciones.
- Documentar rollback.
- Separar seeds sintéticos de migraciones estructurales.

Riesgos: introducir una herramienta nueva sin consenso.

## Observabilidad

Estado: planned

Objetivo: mejorar trazabilidad técnica sin filtrar información sensible.

Tareas:

- Estandarizar logs.
- Añadir métricas de salud.
- Documentar redacción de datos sensibles.

Riesgos: logs con información personal o rutas internas.

## Seguridad y Auditoría

Estado: planned

Objetivo: fortalecer controles de acceso y revisión.

Tareas:

- Revisar auth y roles.
- Añadir checklist de despliegue seguro.
- Documentar reporte de vulnerabilidades.

Riesgos: asumir seguridad productiva antes de una auditoría formal.

## Analítica Geoespacial Avanzada

Estado: planned

Objetivo: explorar análisis espacial más robusto sobre datos autorizados.

Tareas:

- Evaluar clustering espacial.
- Mejorar recomendaciones.
- Añadir benchmarks con datos sintéticos.

Riesgos: inferencias incorrectas con datos incompletos o sesgados.
