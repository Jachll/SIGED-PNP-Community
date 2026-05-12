# Issues iniciales sugeridas

Estas propuestas están listas para copiar a GitHub como issues iniciales.

## 1. Dockerizar entorno completo

Contexto: el arranque local requiere configurar backend, frontend y PostgreSQL/PostGIS por separado.

Objetivo: simplificar instalación local con contenedores.

Tareas:

- Crear Dockerfile para backend.
- Crear Dockerfile o configuración para frontend.
- Crear `docker-compose` con PostgreSQL/PostGIS.
- Documentar variables de entorno.
- Mantener datos reales fuera del compose.

Criterios de aceptación:

- `docker compose up` levanta backend, frontend y base.
- CI no requiere secretos.
- La demo usa datos sintéticos.

## 2. Agregar indicadores operacionales

Contexto: el dashboard puede beneficiarse de métricas operativas resumidas.

Objetivo: definir indicadores claros y verificables.

Tareas:

- Proponer indicadores base.
- Implementar agregaciones en backend.
- Mostrar indicadores en frontend.
- Agregar pruebas con datos sintéticos.

Criterios de aceptación:

- Indicadores documentados.
- Tests backend/frontend actualizados.
- Sin datos reales en fixtures.

## 3. Implementar Libro Operacional con datos sintéticos

Contexto: se necesita una vista ordenada para seguimiento operativo.

Objetivo: crear una primera versión basada en datos sintéticos.

Tareas:

- Definir columnas mínimas.
- Diseñar endpoint o reutilizar contratos existentes.
- Crear vista frontend.
- Agregar tests.

Criterios de aceptación:

- Funciona con datos sintéticos.
- Respeta roles.
- No expone datos sensibles.

## 4. Agregar screenshots seguros con datos sintéticos

Contexto: el README puede comunicar mejor el valor del proyecto con capturas.

Objetivo: crear capturas públicas sin información sensible.

Tareas:

- Preparar entorno con datos sintéticos.
- Usar mapas/capas sintéticas o públicas.
- Capturar dashboard y analítica.
- Agregar nota de seguridad en README.

Criterios de aceptación:

- Capturas no contienen datos reales.
- No aparecen mapas privados.
- Las imágenes tienen permiso de publicación.

## 5. Crear guía de despliegue staging/production

Contexto: el repositorio tiene configuración local, pero falta guía de despliegue seguro.

Objetivo: documentar despliegue con controles básicos.

Tareas:

- Listar variables requeridas.
- Documentar configuración segura de JWT.
- Documentar CORS.
- Documentar desactivación de bootstrap y docs en producción.

Criterios de aceptación:

- Guía clara en `docs/`.
- Sin secretos ni proveedores obligatorios.
- Checklist de seguridad incluido.

## 6. Agregar sample territorial sintético

Contexto: la edición pública no incluye capas reales.

Objetivo: crear una capa territorial mínima totalmente sintética.

Tareas:

- Diseñar geometrías ficticias simples.
- Documentar su origen sintético.
- Integrar demo sin tocar lógica territorial.
- Agregar validación de seguridad de datos.

Criterios de aceptación:

- No usa ubicaciones reales.
- No reemplaza capas institucionales.
- Tests o demo documentada.

## 7. Mejorar analítica temporal

Contexto: la analítica temporal puede incorporar más cortes de lectura.

Objetivo: ampliar visualización temporal sin romper contratos existentes.

Tareas:

- Revisar métricas actuales.
- Proponer cortes por hora, día y semana.
- Agregar pruebas.
- Documentar interpretación.

Criterios de aceptación:

- Funciona con datos sintéticos.
- No cambia endpoints sin discusión.
- Mantiene rendimiento aceptable.

## 8. Agregar reportes PDF/Excel

Contexto: usuarios operativos suelen requerir reportes exportables.

Objetivo: explorar reportes reproducibles y seguros.

Tareas:

- Definir alcance inicial.
- Agregar plantilla con datos sintéticos.
- Documentar riesgos de exportación.
- Agregar pruebas.

Criterios de aceptación:

- No exporta datos reales en fixtures.
- Incluye metadatos de filtros.
- Documenta límites de seguridad.

## 9. Fortalecer auditoría de acciones críticas

Contexto: carga de datos y cambios de seguridad requieren trazabilidad.

Objetivo: mejorar auditoría sin filtrar información sensible.

Tareas:

- Identificar acciones críticas.
- Revisar logs actuales.
- Proponer eventos de auditoría.
- Evitar datos personales o secretos en logs.

Criterios de aceptación:

- Eventos documentados.
- Tests actualizados.
- No se registran secretos.

## 10. Documentar integración de capas PostGIS

Contexto: cada institución debe cargar sus propias capas territoriales.

Objetivo: explicar integración local de capas sin publicar datos privados.

Tareas:

- Documentar formatos soportados.
- Documentar flujo de importación local.
- Agregar checklist de seguridad.
- Explicar fallback y rollback.

Criterios de aceptación:

- Guía clara en `docs/`.
- Advierte no subir capas reales.
- Incluye validaciones mínimas.
