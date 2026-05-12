# API y Auth

Guia de contratos backend para `SIGED-PNP`: autenticacion, roles, endpoints y filtros mas usados.

## Base

- Backend local: `http://localhost:8000`
- Health: `GET /health`
- Docs interactivas: `http://localhost:8000/docs` si `ENABLE_API_DOCS=true`

## Roles

| Rol | Alcance principal |
| --- | --- |
| `admin` | Auth, lectura analitica, cargas, recomendaciones y administracion de usuarios. |
| `analista` | Lectura analitica, cargas y recomendaciones. |
| `consulta` | Lectura de eventos, catalogos, estadisticas y territorio. |

Politicas en codigo:

- `admin`: [`backend/app/security_policy.py`](../backend/app/security_policy.py)
- `auth` y JWT: [`backend/app/security.py`](../backend/app/security.py)

## Bootstrap y login

### Crear el primer administrador

1. Editar `backend/.env`.
2. Activar temporalmente:

```env
ALLOW_BOOTSTRAP_ADMIN=true
```

3. Levantar backend.
4. Ejecutar:

```powershell
curl -X POST http://localhost:8000/auth/bootstrap-admin `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"admin.siged\",\"nombre_completo\":\"Administrador SIGED\",\"password\":\"Admin1234\"}"
```

5. Volver a dejar:

```env
ALLOW_BOOTSTRAP_ADMIN=false
```

### Login

```powershell
curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"admin.siged\",\"password\":\"Admin1234\"}"
```

### Consumir rutas protegidas

```powershell
$token = "eyJ..."

curl http://localhost:8000/eventos `
  -H "Authorization: Bearer $token"
```

## Endpoints publicos

| Metodo | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/health` | Estado del backend y dependencias. |
| `POST` | `/auth/bootstrap-admin` | Provision inicial del primer admin. |
| `POST` | `/auth/login` | Login y emision de JWT. |

## Endpoints para `admin`, `analista`, `consulta`

### Auth

| Metodo | Ruta |
| --- | --- |
| `GET` | `/auth/me` |
| `GET` | `/auth/roles` |

### Eventos y catalogos

| Metodo | Ruta |
| --- | --- |
| `GET` | `/eventos` |
| `GET` | `/eventos/heatmap` |
| `GET` | `/eventos/{id_evento}` |
| `GET` | `/catalogos/delitos` |
| `GET` | `/catalogos/comisarias` |
| `GET` | `/catalogos/distritos` |

### Estadisticas

| Metodo | Ruta |
| --- | --- |
| `GET` | `/estadisticas/por-hora` |
| `GET` | `/estadisticas/por-dia` |
| `GET` | `/estadisticas/por-mes` |
| `GET` | `/estadisticas/por-dia-semana` |

### Territorio

Rutas estables:

| Metodo | Ruta |
| --- | --- |
| `GET` | `/territorio/capas` |
| `GET` | `/territorio/contexto` |
| `GET` | `/territorio/regiones` |
| `GET` | `/territorio/divisiones` |
| `GET` | `/territorio/comisarias` |
| `GET` | `/territorio/jurisdicciones` |
| `GET` | `/territorio/sectores` |
| `GET` | `/territorio/capas/{layer_id}` |
| `GET` | `/territorio/regiones/geojson` |
| `GET` | `/territorio/divisiones/geojson` |
| `GET` | `/territorio/comisarias/geojson` |
| `GET` | `/territorio/jurisdicciones/geojson` |
| `GET` | `/territorio/sectores/geojson` |

Compatibilidad temporal:

| Metodo | Ruta |
| --- | --- |
| `GET` | `/capas/geojson` |
| `GET` | `/capas/geojson/contexto` |
| `GET` | `/capas/geojson/{layer_id}` |

## Endpoints para `admin`, `analista`

### Cargas

| Metodo | Ruta |
| --- | --- |
| `GET` | `/cargas/lotes` |
| `GET` | `/cargas/lotes/{id_lote}` |
| `POST` | `/cargas/lotes` |

### Analisis

| Metodo | Ruta |
| --- | --- |
| `GET` | `/analisis/agregados-espaciales` |
| `GET` | `/analisis/zonas-criticas` |
| `GET` | `/analisis/hotspots` |

### Recomendaciones

| Metodo | Ruta |
| --- | --- |
| `GET` | `/recomendaciones/patrullaje` |
| `POST` | `/recomendaciones/patrullaje/generar` |

## Endpoints solo `admin`

| Metodo | Ruta |
| --- | --- |
| `GET` | `/admin/usuarios` |
| `POST` | `/admin/usuarios` |

## Filtros comunes

Muchos endpoints analiticos aceptan:

- `fecha_inicio`
- `fecha_fin`
- `id_delito`
- `distrito`
- `id_comisaria`
- `region`
- `division`
- `comisaria`
- `jurisdiccion`
- `sector`

Parametros adicionales frecuentes:

- `limite`
- `offset`
- `estado`
- `agrupado_por`
- `min_eventos`
- `turno`
- `fecha_operativa`

## Cargas por API

Endpoint:

- `POST /cargas/lotes`

Formato:

- `multipart/form-data`

Campos:

- `archivo`: `.csv` o `.xlsx`
- `sheet`: hoja Excel opcional
- `observaciones`: texto opcional

## Notas de frontend

El cliente HTTP principal vive en [`frontend/src/services/api.js`](../frontend/src/services/api.js).

Responsabilidades:

- Resolver `API_BASE_URL`
- Adjuntar `Authorization: Bearer <token>`
- Renovar o invalidar sesion local cuando corresponda
- Centralizar errores de auth, cargas, analitica y territorio

## Referencias

- Backend y seguridad: [`backend/app/security.py`](../backend/app/security.py)
- Politicas de rol: [`backend/app/security_policy.py`](../backend/app/security_policy.py)
- Router central: [`backend/app/api/router.py`](../backend/app/api/router.py)
- Runbook territorial: [`docs/migracion_territorial_postgis.md`](migracion_territorial_postgis.md)
