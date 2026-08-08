# ============================================================================
# HERRAMIENTA PERSONALIZADA PARA CREWAI
# ============================================================================
# Las herramientas (Tools) son las "habilidades" que le damos a los agentes.
# Esta herramienta permite buscar información en internet usando DuckDuckGo.
# ============================================================================

from crewai.tools import BaseTool  # Clase base para crear herramientas custom
from typing import Type
from pydantic import BaseModel, Field  # Para validar los parámetros de entrada
from ddgs import DDGS  # Motor de búsqueda DuckDuckGo (gratis, sin API key)


# PASO 1: Definir el esquema de entrada
# ======================================
# Pydantic valida que el agente envíe los parámetros correctos
class InternetSearchToolInput(BaseModel):
    """Define qué parámetros recibe la herramienta."""
    query: str = Field(..., description="La consulta de búsqueda para encontrar información en internet.")


# PASO 2: Crear la herramienta heredando de BaseTool
# ===================================================
class InternetSearchTool(BaseTool):
    # El 'name' es cómo el agente identifica la herramienta
    name: str = "Búsqueda en Internet"
    
    # La 'description' es CRUCIAL: el LLM la lee para decidir cuándo usar la herramienta
    description: str = (
        "Herramienta para buscar información actualizada en internet sobre destinos turísticos, "
        "restaurantes, atracciones, vuelos, alojamiento y cualquier otro dato relacionado con viajes. "
        "Proporciona resultados actualizados y relevantes."
    )
    
    # El 'args_schema' define qué parámetros espera recibir
    args_schema: Type[BaseModel] = InternetSearchToolInput

    # PASO 3: Implementar el método _run()
    # =====================================
    # Este método se ejecuta cuando el agente decide usar la herramienta
    def _run(self, query: str) -> str:
        """
        Ejecuta la búsqueda en internet y retorna resultados formateados.
        
        Args:
            query: La consulta de búsqueda que el agente quiere realizar
            
        Returns:
            str: Resultados en formato texto que el agente puede leer
        """
        try:
            # Inicializar DuckDuckGo y realizar búsqueda
            with DDGS() as ddgs:
                # Obtener máximo 5 resultados de búsqueda
                results = list(ddgs.text(query, max_results=5))
                
                # Si no hay resultados, informar al agente
                if not results:
                    return f"No se encontraron resultados para: {query}"
                
                # Formatear los resultados de forma legible para el agente
                formatted_results = []
                for idx, result in enumerate(results, 1):
                    title = result.get('title', 'Sin título')
                    body = result.get('body', 'Sin descripción')  # Snippet/resumen
                    href = result.get('href', '')  # URL de la fuente
                    
                    # Formato: Número. Título + Descripción + URL
                    formatted_results.append(
                        f"{idx}. {title}\n"
                        f"   {body}\n"
                        f"   Fuente: {href}\n"
                    )
                
                # Retornar todos los resultados como un solo string
                return "\n".join(formatted_results)
                
        except Exception as e:
            # Si algo falla, informar el error al agente
            return f"Error al realizar la búsqueda: {str(e)}"
