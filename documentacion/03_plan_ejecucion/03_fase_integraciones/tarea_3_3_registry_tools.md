# 🔹 Tarea 3.3 — Envoltorios de Herramientas para el LLM (`tools/registry.py`)

## 🎯 Objetivo
Registrar las herramientas del sistema definiendo su esquema JSON (parámetros y descripciones) para permitir su invocación mediante Tool Calling desde el LLM.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `tools/registry.py`:**
   ```python
   TOOLS_SCHEMA = [
       {
           "type": "function",
           "function": {
               "name": "get_calendar_events",
               "description": "Obtiene la lista de eventos guardados en Google Calendar para una fecha concreta.",
               "parameters": {
                   "type": "object",
                   "properties": {
                       "date_str": {
                           "type": "string",
                           "description": "Fecha en formato YYYY-MM-DD"
                       }
                   },
                   "required": ["date_str"]
               }
           }
       },
       {
           "type": "function",
           "function": {
               "name": "create_calendar_event",
               "description": "Crea una nueva cita o evento en Google Calendar.",
               "parameters": {
                   "type": "object",
                   "properties": {
                       "summary": {"type": "string", "description": "Título de la reunión o evento"},
                       "start_iso": {"type": "string", "description": "Hora de inicio en ISO format YYYY-MM-DDTHH:MM:SS"},
                       "end_iso": {"type": "string", "description": "Hora de fin en ISO format YYYY-MM-DDTHH:MM:SS"},
                       "description": {"type": "string", "description": "Detalles adicionales"}
                   },
                   "required": ["summary", "start_iso", "end_iso"]
               }
           }
       },
       {
           "type": "function",
           "function": {
               "name": "get_next_workout",
               "description": "Obtiene la rutina de gimnasio que le toca realizar hoy al usuario.",
               "parameters": {"type": "object", "properties": {}}
           }
       }
   ]
   ```

---

## ✅ Verificación de la Tarea
- Verificar que el objeto `TOOLS_SCHEMA` sea una lista válida de diccionarios Python compatibles con la especificación de Function Calling de OpenAI/Gemini.
