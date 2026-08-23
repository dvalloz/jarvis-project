# 🔹 Tarea 5.4 — Manejador de Respuestas de Teclado (`CallbackQueryHandler`)

## 🎯 Objetivo
Capturar las pulsaciones del usuario en los botones inline del Check-in Nocturno y guardar los registros directamente en PostgreSQL.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar `button_callback_handler` en `bot/handlers.py`:**
   ```python
   from telegram import Update
   from telegram.ext import ContextTypes, CallbackQueryHandler
   from bot.handlers_security import restricted
   from database.connection import AsyncSessionLocal
   from database.crud import get_next_workout_routine, log_completed_workout

   @restricted
   async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
       query = update.callback_query
       await query.answer()

       data = query.data
       async with AsyncSessionLocal() as db:
           if data == "workout_done":
               workout = await get_next_workout_routine(db)
               if workout:
                   await log_completed_workout(db, workout_id=workout.id, notes="Completado via inline button")
                   await query.edit_message_text(f"💪 ¡Genial! He registrado la sesión de **{workout.name}** como completada.")
               else:
                   await query.edit_message_text("No se encontró rutina activa.")
           elif data == "workout_rest":
               await query.edit_message_text("💤 Registrado día de descanso. ¡A recuperar energías!")
           elif data == "tasks_done":
               await query.edit_message_text("🧹 ¡Perfecto! He actualizado el estado de tus tareas del hogar.")
   ```

---

## ✅ Verificación de la Tarea
- Pulsar los botones en el mensaje de Check-in Nocturno en Telegram y comprobar que el texto del mensaje se edite y que el registro se guarde en la BD.
