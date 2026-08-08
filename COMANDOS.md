# ================================================================
# Frontend con React + Vite
- Runtime: Node.js v26
# 1. Entrar a la carpeta del frontend
cd "Frontend-Proyecto-Planificador-de-Viajes"
# 2. Instalar dependencias (SOLO la primera vez, o si cambia package.json)
npm install
# 3. Levantar el servidor de desarrollo
npm run dev

Luego abre http://localhost:5173 en el navegador.

# ================================================================

# Levantamiento en Local
## Comando para levantar el endpoint en Local
uv sync

uv run uvicorn backend_proyecto_planificador_de_viajes.main:app --app-dir src --host 127.0.0.1 --port 8005 --reload

# ================================================================

# Despliegue sobre VPS por Contenedor de Docker
## Comando para Loguearte en Docker Desktop
docker login

docker buildx build \
  --platform linux/amd64 \
  -t kevininofuentecolque/app-crewai-conversacional-backend-ai-engineer-13:latest \
  --push \
  .




cd "Backend-Proyecto-Planificador-de-Viajes-Hierarchical"
uv sync    # crea su PROPIO .venv (obligatorio la primera vez)
uv run uvicorn backend_proyecto_planificador_de_viajes.main:app --app-dir src --host 127.0.0.1 --port 8005 --reload