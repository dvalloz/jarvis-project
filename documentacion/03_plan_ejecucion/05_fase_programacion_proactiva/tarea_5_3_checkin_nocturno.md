# 🔹 Tarea 5.3 — Implementación del Check-in Nocturno (Cron: 21:30 PM)

## 🎯 Objetivo
Configurar el envío del mensaje de seguimiento nocturno automático adjuntando un teclado interactivo (*InlineKeyboardMarkup*).

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar `nightly_checkin_job` en `bot/scheduler.py`:**
   ```python
   from telegram import InlineKeyboardButton, InlineKeyboardMarkup
   from config.settings import settings

   async def nightly_checkin_job(app):
       keyboard = [
           [InlineKeyboardButton("✅ Entreno Hecho", callback_data="workout_done")],
           [InlineKeyboardButton("💤 Día de Descanso", callback_data="workout_rest")],
           [InlineKeyboardButton("🧹 Tareas Completadas", callback_data="tasks_done")]
       ]
       reply_markup = InlineKeyboardMarkup(keyboard)

       await app.bot.send_message(
           chat_id=settings.telegram_user_id,
           text="🌙 **CHECK-IN NOCTURNO**\n¿Cómo ha ido el día de hoy? Marca tus hábitos con un toque:",
           reply_markup=reply_markup,
           parse_mode="Markdown"
       )
   ```

---

## ✅ Verificación de la Tarea
- Invocar el job manualmente y comprobar que el mensaje se reciba con los tres botones interactivos en Telegram.
