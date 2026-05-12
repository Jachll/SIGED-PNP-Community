# Fase 3: tipado progresivo y contratos frontend

## Recomendacion

Si el frontend sigue creciendo en Fase 3, conviene endurecer contratos en dos capas:

1. Contratos de runtime en `services/` y `utils/normalizers`
2. Tipado progresivo en hooks y vistas de mayor acoplamiento

## Plan sugerido

### Fase 3.1

- Mantener JSX, pero agregar `JSDoc` a respuestas clave (`auth`, `territorio`, `dashboard`, `analitica`).
- Centralizar normalizadores por dominio para evitar que cada vista reinterprete payloads.
- Consolidar estados de carga en un shape comun: `kind`, `tone`, `status`, `message`.

### Fase 3.2

- Activar `checkJs` o migrar primero `services/`, `hooks/` y `utils/` a `*.ts`.
- Tipar filtros compartidos, contexto territorial, errores de carga y respuestas de mapas.
- Tipar helpers puros antes que componentes visuales para reducir riesgo.

### Fase 3.3

- Migrar `AuthContext`, `useProtectedCatalogView`, `useOperationalAnalyticsView` y `useGeoBoundaryLayers` a TypeScript.
- Definir unions para roles, modos territoriales y estados de vista.
- Usar adaptadores de API tipados para que las páginas consuman modelos internos estables.

## Orden recomendado

1. `src/services/`
2. `src/utils/`
3. `src/hooks/`
4. `src/auth/`
5. `src/pages/` y `src/components/`

## Riesgos que evita

- Accesos a `null` o `undefined` en fallback territoriales
- Divergencia entre contratos backend/frontend
- Mensajes de error inconsistentes por vista
- Reglas de acceso por rol repetidas en distintos componentes
