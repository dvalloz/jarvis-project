# 🔹 Tarea 5.2 — Implementación del Briefing Matutino (Cron: 08:00 AM)

## 🎯 Objetivo
Desarrollar la función programada que recopila eventos del día, rutina correspondiente y tareas del hogar para generar un informe consolidado enviado a las 08:00 AM.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar `morning_briefing_job` en `bot/scheduler.py`:**
   ```python
   from datetime import date
   from database.connection import AsyncSessionLocal
   from database.crud import get_next_workout_routine, get_due_recurring_tasks
   from tools.calendar_tools import get_day_events
   from config.settings import settings

   async def morning_briefing_job(app):
       today = date.today()
       events = get_day_events(today)
       
       async with AsyncSessionLocal() as db:
           workout = await get_next_workout_routine(db)
           tasks = await get_due_recurring_tasks(db)

       prompt = f"""
   Genera un Briefing Matutino conciso con el siguiente contexto:
   - Eventos de Google Calendar: {events}
   - Rutina de gimnasio propuesta para hoy: {workout.name if workout else 'Descanso'} ({workout.target_muscles if workout else ''})
   - Tareas periódicas que vencen hoy: {[t.title for t in tasks]}
   """
   
       from agent.engine import run_agent
       summary = await run_agent(prompt)

       await app.bot.send_message(
           chat_id=settings.telegram_user_id,
           text=f"☀️ **BRIEFING MATUTINO ({today.strftime('%d/%m/%Y')})**\n\n{summary}",
           parse_mode="Markdown"
       )
   ```

---

## ✅ Verificación de la Tarea
- Forzar la ejecución manual del job mediante script y confirmar la recepción del briefing en el chat de Telegram.
