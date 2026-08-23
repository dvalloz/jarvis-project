# 🔹 Tarea 4.3 — Diseño del System Prompt (`agent/prompts.py`)

## 🎯 Objetivo
Definir las instrucciones del sistema (*System Prompt*) fijando la personalidad, restricciones de formato y contexto temporal del asistente.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `agent/prompts.py`:**
   ```python
   from datetime import datetime
   import pytz
   from config.settings import settings

   def get_system_prompt() -> str:
       tz = pytz.timezone(settings.timezone)
       now = datetime.now(tz)
       current_date_str = now.strftime("%Y-%m-%d")
       current_time_str = now.strftime("%H:%M")
       day_name = now.strftime("%A")

       return f"""
   Eres Jarvis, un asistente personal inteligente, proactivo, conciso y directo para Telegram.
   Tu objetivo es ayudar al usuario a gestionar su agenda de Google Calendar, sus rutinas de gimnasio y sus tareas del hogar.

   Contexto Temporal Actual:
   - Fecha de hoy: {current_date_str} ({day_name})
   - Hora actual: {current_time_str}
   - Zona Horaria: {settings.timezone}

   Reglas de Comportamiento:
   1. Responde de forma breve y estructurada, ideal para lectura rápida en pantallas de teléfonos móviles.
   2. Usa emojis apropiados para mejorar la claridad de lectura.
   3. Cuando el usuario te pida consultar eventos o rutinas, utiliza siempre tus herramientas registradas (*tool calling*) en lugar de suponer información.
   4. Sé proactivo y sugerente en tus respuestas.
   """
   ```

---

## ✅ Verificación de la Tarea
- Verificar que `get_system_prompt()` devuelva la fecha y hora actualizada dinámicamente con la zona horaria `Europe/Madrid`.
