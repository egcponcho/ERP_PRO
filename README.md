# ERP PRO

ERP modular y configurable, construido desde cero tomando como referencia
[egcponcho/ERP](https://github.com/egcponcho/ERP). De ese repositorio se trajo solo lo
probado y transversal; ningún módulo de negocio todavía.

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic y PostgreSQL (SQLite para desarrollo y pruebas).
- **Frontend:** Vue 3 + Vite, sin librerías de componentes; tema claro y oscuro, accesible con teclado y lector de pantalla.
- **Varias organizaciones:** cada tabla lleva `organizacion_id` y el ORM aísla los datos de cada una.
- **Identificadores y textos en español.**

## Qué trae

| Pieza | Dónde | Para qué |
| --- | --- | --- |
| Organizaciones | `backend/app/core/organizacion.py` | Mixin `DeOrganizacion`: el ORM filtra y asigna la organización de la sesión |
| Errores de negocio | `core/errores.py`, `web/errores.py` | `ErrorNegocio` → `{mensaje, codigo, detalle}` con su código HTTP |
| Concurrencia | `core/modelo.py` | `ConVersion`: un cambio sobre un registro desactualizado responde 409 |
| Integridad | `core/integridad.py` | Referencias de la misma organización; unicidad y llaves foráneas como 409 |
| Motor de atributos | `backend/app/atributos/` | Características tipadas definidas en la configuración, plantillas heredables |
| Componentes | `frontend/src/componentes/` | `TablaDatos`, `PanelEnLinea`, `BotonConfirmar`, `CampoAtributo`, `SelectorReferencia`… |
| Sistema de diseño | `design-system/MASTER.md`, `frontend/src/styles.css` | Tokens de color, tipografía y espaciado |

Cómo usar cada pieza al crear un módulo: [docs/NUCLEO.md](docs/NUCLEO.md).

## Estructura

```
backend/
  app/
    core/          base de datos, organización, errores, integridad, concurrencia, referencias
    atributos/     motor de atributos: modelos · valores · esquema · configuracion · api
    web/           sesión de la petición y manejadores de errores
    modulos/       aquí entra cada módulo de negocio
    modelos/       importar_todo() para Alembic y el arranque
    main.py
  alembic/         migraciones (0001_inicial)
  tests/           pruebas del núcleo y del motor, con un módulo de ejemplo (tests/demo.py)
frontend/          interfaz en Vue 3
design-system/     sistema de diseño
docs/NUCLEO.md     guía para construir módulos sobre el núcleo
```

## Cómo empezar

Necesita Python 3.12+ y Node.js 20+.

```bash
# Terminal 1: la API en http://localhost:8000
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head                                  # crea la base (SQLite: backend/erp_pro.db)
python -m app.atributos.instalacion                   # opcional: magnitudes y unidades sugeridas
uvicorn app.main:app --reload

# Terminal 2: la interfaz en http://localhost:5173 (redirige /api al puerto 8000)
cd frontend
npm install
npm run dev
```

Con PostgreSQL: `DATABASE_URL=postgresql+psycopg://usuario:clave@host/base`.
Para usar un solo servidor: `npm run build` dentro de `frontend` y la API sirve la interfaz compilada en http://localhost:8000.

## En la nube (Fly.io)

`fly.toml` compila el `Dockerfile` (interfaz + API en un solo contenedor) y revisa `/api/salud`.
Al arrancar, `backend/arrancar.sh` aplica las migraciones y, con `CARGAR_CONFIG_BASE=1`, agrega las
magnitudes y unidades sugeridas que falten.

```bash
fly auth login
fly launch --copy-config --no-deploy    # usa este fly.toml; elija un nombre libre y la región
fly secrets set DATABASE_URL="postgresql://usuario:clave@host/base?sslmode=require"
fly deploy
```

`fly launch` reescribe `app` y `primary_region` en `fly.toml`: súbalo al repositorio. También se puede
desplegar a mano desde GitHub (*Actions → Desplegar en Fly.io*) con el secreto `FLY_API_TOKEN`
(`fly tokens create deploy -x 999999h`).

## Interfaz en Netlify

Netlify sirve archivos estáticos y funciones cortas: no puede correr la API (Python, FastAPI) ni la
base PostgreSQL. Por eso `netlify.toml` publica solo la interfaz compilada (`frontend/dist`) y reenvía
`/api/*` a la API desplegada en Fly.io (`https://erp-pro.fly.dev`). Si la API queda en otra
dirección, cambie la primera regla de `netlify.toml`.

1. Despliegue la API en Fly.io (sección anterior).
2. En Netlify, con el sitio ya conectado al repositorio, no hace falta configurar nada: toma
   `netlify.toml` en cada push a `main`.

## Pruebas

```bash
cd backend
pytest                                                                   # SQLite en memoria
TEST_DATABASE_URL=postgresql+psycopg://erp@localhost/erp_test pytest      # PostgreSQL (la base se vacía)
ruff check .

cd ../frontend && npm run lint && npm run build
```

GitHub Actions corre todo esto en cada push y en cada PR (`.github/workflows/ci.yml`).
