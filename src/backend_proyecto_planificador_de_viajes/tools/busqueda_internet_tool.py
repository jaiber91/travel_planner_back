# ============================================================================
# HERRAMIENTA PERSONALIZADA PARA CREWAI — BÚSQUEDA EN INTERNET CON TAVILY
# ============================================================================
# Igual que custom_tool.py (DuckDuckGo), pero usando Tavily, que está pensado
# para agentes de IA: devuelve contenido extraído + una respuesta sintetizada
# y resultados ordenados por relevancia.
#
# Requisitos:
#   - Paquete: tavily-python  (declarado en pyproject.toml)
#   - Variable de entorno: TAVILY_API_KEY  (en el archivo .env)
#     Consíguela gratis en https://tavily.com
#
# Autor: Ing. Kevin Inofuente Colque - DataPath
# ============================================================================

import os
from typing import Type

from crewai.tools import BaseTool  # Clase base para crear herramientas custom
from pydantic import BaseModel, Field  # Para validar los parámetros de entrada
from tavily import TavilyClient  # SDK oficial de Tavily


# PASO 1: Definir el esquema de entrada
# ======================================
class InternetSearchToolInput(BaseModel):
    """Define qué parámetros recibe la herramienta."""
    query: str = Field(
        ...,
        description="La consulta de búsqueda para encontrar información en internet.",
    )


# PASO 2: Crear la herramienta heredando de BaseTool
# ===================================================
class TavilyInternetSearchTool(BaseTool):
    # El 'name' es cómo el agente identifica la herramienta
    name: str = "Búsqueda en Internet"

    # La 'description' es CRUCIAL: el LLM la lee para decidir cuándo usarla
    description: str = (
        "Herramienta para buscar información actualizada en internet sobre destinos turísticos, "
        "restaurantes, atracciones, vuelos, alojamiento y cualquier otro dato relacionado con viajes. "
        "Proporciona resultados actualizados y relevantes usando el motor Tavily."
    )

    # El 'args_schema' define qué parámetros espera recibir
    args_schema: Type[BaseModel] = InternetSearchToolInput

    # PASO 3: Implementar el método _run()
    # =====================================
    def _run(self, query: str) -> str:
        """
        Ejecuta la búsqueda con Tavily y retorna resultados formateados.

        Args:
            query: La consulta de búsqueda que el agente quiere realizar

        Returns:
            str: Resultados en formato texto que el agente puede leer
        """
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return (
                "Error: falta la variable TAVILY_API_KEY en el archivo .env. "
                "Obtén una API key gratis en https://tavily.com"
            )

        try:
            client = TavilyClient(api_key=api_key)

            # include_answer=True: Tavily sintetiza una respuesta breve a partir
            # de las fuentes; muy útil como resumen inicial para el agente.
            # search_depth="advanced": búsqueda más profunda y relevante.
            response = client.search(
                query=query,
                max_results=5,
                search_depth="advanced",
                include_answer=True,
            )

            results = response.get("results", [])
            answer = response.get("answer")

            if not results and not answer:
                return f"No se encontraron resultados para: {query}"

            partes = []

            # Respuesta sintetizada por Tavily (si la hay)
            if answer:
                partes.append(f"Resumen: {answer}\n")

            # Resultados individuales con su fuente
            for idx, result in enumerate(results, 1):
                title = result.get("title", "Sin título")
                content = result.get("content", "Sin descripción")
                url = result.get("url", "")

                partes.append(
                    f"{idx}. {title}\n"
                    f"   {content}\n"
                    f"   Fuente: {url}\n"
                )

            return "\n".join(partes)

        except Exception as e:
            # Si algo falla, informar el error al agente
            return f"Error al realizar la búsqueda: {str(e)}"
