# 🔹 Tarea 4.2 — Configuración del Motor del Agente (`agent/engine.py`)

## 🎯 Objetivo
Construir el motor principal de orquestación entre las entradas del usuario, el modelo de lenguaje (LLM) y el sistema de ejecución de herramientas (*Tool Calling*).

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar `agent/engine.py`:**
   ```python
   import json
   from openai import AsyncOpenAI
   from config.settings import settings
   from tools.registry import TOOLS_SCHEMA
   from tools.calendar_tools import get_day_events, create_calendar_event
   from database.connection import AsyncSessionLocal
   from database.crud import get_next_workout_routine
   from agent.prompts import get_system_prompt

   client = AsyncOpenAI(api_key=settings.openai_api_key)

   async def run_agent(user_message: str) -> str:
       system_prompt = get_system_prompt()
       messages = [
           {"role": "system", "content": system_prompt},
           {"role": "user", "content": user_message}
       ]

       response = await client.chat.completions.create(
           model="gpt-4o-mini",
           messages=messages,
           tools=TOOLS_SCHEMA,
           tool_choice="auto"
       )

       response_message = response.choices[0].message
       tool_calls = response_message.tool_calls

       if tool_calls:
           messages.append(response_message)
           for tool_call in tool_calls:
               function_name = tool_call.function.name
               args = json.loads(tool_call.function.arguments)
               tool_result = ""

               if function_name == "get_calendar_events":
                   tool_result = str(get_day_events(args.get("date_str")))
               elif function_name == "get_next_workout":
                   async with AsyncSessionLocal() as db:
                       workout = await get_next_workout_routine(db)
                       tool_result = f"Rutina: {workout.name} ({workout.target_muscles})" if workout else "No hay rutinas."

               messages.append({
                   "tool_call_id": tool_call.id,
                   "role": "tool",
                   "name": function_name,
                   "content": tool_result
               })

           second_response = await client.chat.completions.create(
               model="gpt-4o-mini",
               messages=messages
           )
           return second_response.choices[0].message.content

       return response_message.content
   ```

---

## ✅ Verificación de la Tarea
- Invocar `run_agent("¿Qué me toca entrenar hoy?")` en un entorno de desarrollo y verificar que invoque la herramienta `get_next_workout` y retorne la respuesta redactada en lenguaje natural.
