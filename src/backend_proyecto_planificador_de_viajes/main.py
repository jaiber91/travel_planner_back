# src/travel_crew_backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import JSONResponse
from datetime import date
import os
from openai import AsyncOpenAI

# Usamos una importación relativa porque 'crew.py' está en el mismo directorio.
from .crew import TravelCrew

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API del Asistente de Viajes",
    description="Una API para planificar itinerarios de viaje personalizados usando un equipo de agentes de IA (CrewAI).",
    version="1.0.0"
)

# --- CORS ---
# Permite peticiones desde cualquier origen.
# En producción puedes restringirlo a tu dominio del frontend:
#   allow_origins=["https://tu-frontend.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TripRequest(BaseModel):
    prompt: str

# --- Función de Limpieza ---
# Esta función eliminará los artefactos comunes del LLM
def clean_llm_output(text: str) -> str:
    cleaned_text = text.replace("∗", "").replace("ˊ", "")
    # Puedes añadir más reemplazos si encuentras otros artefactos
    return cleaned_text

# --- Clasificador de intención ---
# Llama al LLM con un prompt mínimo para decidir si el usuario quiere planificar
# un viaje o simplemente está chateando. Devuelve (es_viaje, respuesta_conversacional).
# Si es_viaje=True, respuesta_conversacional es None y se lanza el crew.
# Si es_viaje=False, respuesta_conversacional es el mensaje amigable para el usuario.
async def classify_intent(user_prompt: str) -> tuple[bool, str | None]:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_msg = (
        "Eres el portero de un asistente especializado en planificación de viajes. "
        "Tu única tarea es decidir si el mensaje del usuario es una solicitud para "
        "planificar o consultar sobre un viaje (destino, itinerario, fechas, actividades, "
        "vuelos, hoteles, presupuesto, etc.).\n\n"
        "Responde ÚNICAMENTE con uno de estos dos formatos:\n"
        "  TRIP: <sí|no>\n"
        "  REPLY: <mensaje amigable en el idioma del usuario>\n\n"
        "Si es una solicitud de viaje, REPLY debe estar vacío (solo pon un guión).\n"
        "Si NO es una solicitud de viaje, REPLY debe ser una respuesta conversacional "
        "breve y amigable que redirija al usuario hacia la planificación de viajes.\n\n"
        "Ejemplos:\n"
        "  Usuario: 'hola' → TRIP: no / REPLY: ¡Hola! Soy tu asistente de viajes. "
        "Cuéntame, ¿a dónde te gustaría viajar?\n"
        "  Usuario: 'quiero ir a Tokio 7 días en marzo' → TRIP: sí / REPLY: -\n"
        "  Usuario: '¿cuál es la capital de Francia?' → TRIP: no / REPLY: ¡Buena "
        "pregunta! París es la capital de Francia, y también es un destino de viaje "
        "increíble. ¿Te gustaría que te planificara un viaje allí?\n"
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",  # modelo ligero para clasificación rápida y económica
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=200,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    print(f"🔍 Clasificador de intención: {raw}")

    # Parsear las dos líneas devueltas por el LLM
    is_trip = False
    reply_msg = None
    for line in raw.splitlines():
        if line.upper().startswith("TRIP:"):
            is_trip = "sí" in line.lower() or "si" in line.lower() or "yes" in line.lower()
        elif line.upper().startswith("REPLY:"):
            candidate = line[6:].strip()
            if candidate and candidate != "-":
                reply_msg = candidate

    if not is_trip and not reply_msg:
        reply_msg = "¡Hola! Soy tu asistente de viajes. Cuéntame, ¿a dónde te gustaría viajar?"

    return is_trip, reply_msg

@app.post("/plan-trip") #Primer Endpoint.
async def plan_trip_endpoint(request: TripRequest):
    """
    Recibe una petición de viaje y devuelve un itinerario generado por el Crew de IA,
    listo para mostrarse en el chat y para ser descargado.
    """
    try:
        # --- Clasificar intención antes de lanzar el crew ---
        is_trip, conversational_reply = await classify_intent(request.prompt)

        if not is_trip:
            print(f"💬 Mensaje conversacional detectado, respondiendo sin lanzar el crew.")
            return {
                "chat_response": conversational_reply,
                "download_content": "",
                "download_filename": "",
            }

        inputs = {
            'trip_request': request.prompt,
            # Fecha de hoy: el agente de agenda la usa para resolver fechas relativas
            'fecha_actual': date.today().isoformat(),
        }
        
        print(f"🚀 Ejecutando el crew para la petición: {request.prompt}")
        travel_crew = TravelCrew()
        # crewai 1.14+: dentro de un endpoint async hay que usar kickoff_async,
        # no kickoff (síncrono), o lanza "invoked synchronously from within a running event loop".
        result = await travel_crew.crew().kickoff_async(inputs=inputs)
        print(f"✅ Crew finalizado. Procesando resultado.")

        # 1. Obtener el resultado final y limpiarlo para el chat
        final_chat_response = clean_llm_output(result.raw)

        # 2. Leer el contenido del archivo .md para la descarga
        download_content = ""
        filename = "itinerary.md"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                download_content = f.read()
        except FileNotFoundError:
            print(f"⚠️  Advertencia: No se encontró el archivo '{filename}'. La descarga no estará disponible.")
            download_content = final_chat_response # Como fallback, usamos la respuesta del chat

        # 3. Construir la respuesta JSON estructurada
        structured_response = {
            "chat_response": final_chat_response,
            "download_content": download_content,
            "download_filename": filename
        }
        
        return structured_response

    except Exception as e:
        print(f"❌ Error durante la ejecución del crew: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": "Ocurrió un error interno al procesar tu solicitud.", "details": str(e)}
        )

@app.get("/") #Segundo Endpoint.
def read_root():
    return {"status": "El servidor del Asistente de Viajes IA está funcionando."}