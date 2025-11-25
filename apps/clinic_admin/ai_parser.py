# apps/clinic_admin/ai_parser.py

import os
import re
import json
import logging
from datetime import datetime
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger('apps')

# Configuración de API Key (Mejor usar variables de entorno)
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY') or getattr(settings, "GEMINI_API_KEY", None)

# 👇 AGREGA ESTO SI SIGUE FALLANDO 👇
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = "AIzaSyAeDp7UlSvee0Sm25TkUmYiE9KgEihl8DA" # <--- TU CLAVE REAL AQUÍ

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- PROMPT ENTRENADO PARA CLÍNICA ---
PROMPT_MAESTRO = """
Eres un asistente experto en SQL y análisis de datos para una Clínica de Salud Mental. 
Tu trabajo es convertir un pedido en lenguaje natural a un JSON de filtros.

ESQUEMA JSON DE SALIDA (Usa solo estas claves):
{
  "report_type": "pdf" | "csv",
  "psychologist_search": "nombre parcial del psicólogo",
  "patient_search": "nombre parcial del paciente",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}

REGLAS DE NEGOCIO:
1. Si pide "excel", devuelve "csv". Por defecto es "pdf".
2. "Semana pasada", "este mes", "ayer" -> Calcula las fechas exactas considerando que HOY es {HOY}.
3. "Ventas", "cobros", "ingresos" -> Se refiere a los PAGOS.
4. Si menciona un nombre sin especificar rol, intenta deducirlo o búscalo como paciente por defecto.

EJEMPLOS:
User: "Reporte de ingresos del Dr. Ernesto de noviembre en excel"
AI: {"report_type": "csv", "psychologist_search": "Ernesto", "start_date": "2025-11-01", "end_date": "2025-11-30"}

User: "Pagos del paciente Juan Perez"
AI: {"report_type": "pdf", "patient_search": "Juan Perez"}
"""

def parse_prompt_to_filters(prompt_text: str) -> dict:
    """Traduce lenguaje natural a filtros de Django."""
    if not GOOGLE_API_KEY:
        logger.error("❌ GEMINI_API_KEY no configurada")
        return {}

    try:
        # Usamos Flash por ser rápido
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Inyectamos la fecha de hoy para que entienda "ayer" o "semana pasada"
        hoy = datetime.now().strftime('%Y-%m-%d')
        prompt_final = PROMPT_MAESTRO.replace("{HOY}", hoy)
        
        full_prompt = f"{prompt_final}\n\nUser: \"{prompt_text}\"\nAI JSON:"
        
        response = model.generate_content(full_prompt)
        
        # Limpieza del JSON (a veces la IA mete comillas extra)
        text = response.text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(0))
        return {}

    except Exception as e:
        logger.error(f"Error IA: {e}")
        return {}