# Backend — Planificador de Viajes IA (CrewAI + FastAPI)

Backend del planificador de viajes conversacional. Expone una **API FastAPI** que
ejecuta un **crew de 6 agentes de CrewAI** para investigar un destino y generar un
itinerario personalizado día por día, agendándolo además en Google Calendar.

## Requisitos

- Python 3.10–3.12
- [uv](https://docs.astral.sh/uv/) para gestionar dependencias
- Claves en el archivo `.env` (ver `.env.example`):
  - `OPENAI_API_KEY` — modelo LLM.
  - `TAVILY_API_KEY` — búsqueda en internet de los agentes ([gratis en tavily.com](https://tavily.com)).
  - `CREWAI_PLATFORM_INTEGRATION_TOKEN` — integración de Google Calendar (Settings → Integrations en app.crewai.com).

## Puesta en marcha

```bash
cp .env.example .env      # rellena tus claves
uv sync                   # crea el .venv e instala dependencias
uv run uvicorn backend_proyecto_planificador_de_viajes.main:app \
  --app-dir src --host 127.0.0.1 --port 8005 --reload
```

El servidor queda en `http://localhost:8005`.

## API

| Método | Ruta          | Descripción |
|--------|---------------|-------------|
| `GET`  | `/`           | Healthcheck. |
| `POST` | `/plan-trip`  | Recibe `{ "prompt": "..." }` y devuelve el itinerario. |

Respuesta de `/plan-trip`:

```json
{
  "chat_response": "…itinerario en markdown…",
  "download_content": "…documento completo en markdown…",
  "download_filename": "itinerary.md"
}
```

## El crew (6 agentes, proceso secuencial)

Definido en `src/backend_proyecto_planificador_de_viajes/crew.py`, con los roles y
tareas en `config/agents.yaml` y `config/tasks.yaml`.

| # | Agente | Herramienta | Función |
|---|--------|-------------|---------|
| 1 | Experto cultural | Búsqueda (Tavily) | Atracciones, museos, sitios históricos. |
| 2 | Gourmet local | Búsqueda (Tavily) | Restaurantes y gastronomía típica. |
| 3 | Logística | Búsqueda (Tavily) | Vuelos, hoteles, transporte, presupuesto. |
| 4 | Planificador de itinerario | — | Organiza todo en un plan día por día. |
| 5 | Gestor de agenda | Google Calendar | Crea un evento por cada día del viaje. |
| 6 | Redactor de viajes | — | Escribe el documento final (`itinerary.md`). |

Flujo: `cultura → gastronomía → logística → itinerario → agenda → redacción`.

## Herramientas de búsqueda

- **`tools/busqueda_internet_tool.py`** — herramienta **activa**, basada en **Tavily**
  (mejor para agentes de IA: contenido extraído + respuesta sintetizada).
- **`tools/custom_tool.py`** — alternativa con **DuckDuckGo** (`ddgs`), gratis y sin
  API key. Para volver a ella, edita el import y `self.search_tool` en `crew.py`.

## Estructura

```
src/backend_proyecto_planificador_de_viajes/
├── main.py                  # API FastAPI (endpoint /plan-trip)
├── crew.py                  # Definición del crew (agentes + tareas)
├── config/
│   ├── agents.yaml          # Roles, objetivos y backstories
│   └── tasks.yaml           # Descripciones y outputs esperados
└── tools/
    ├── busqueda_internet_tool.py   # Búsqueda con Tavily (activa)
    └── custom_tool.py              # Búsqueda con DuckDuckGo (alternativa)
```

## Notas

- El endpoint usa `kickoff_async` (requerido dentro del event loop de FastAPI).
- El tracing interactivo de CrewAI está desactivado (`tracing=False`) para que no
  bloquee las requests en el servidor.
- El itinerario final se guarda en `itinerary.md` (vía `output_file` de la tarea de
  redacción) y se devuelve en `download_content`.
