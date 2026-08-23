# 🔹 Tarea 4.4 — Enrutamiento de Mensajes y Comandos Rápidos

## 🎯 Objetivo
Configurar los manejadores de eventos (`CommandHandler` y `MessageHandler`) de `python-telegram-bot` para conectar el bot con el motor del agente y ofrecer comandos rápidos.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar Handlers en `bot/handlers.py`:**
   ```python
   from telegram import Update
   from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
   from bot.handlers_security import restricted
   from agent.engine import run_agent

   @restricted
   async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
       await update.message.reply_text("👋 ¡Hola! Soy Jarvis, tu asistente personal. ¿En qué te puedo ayudar hoy?")

   @restricted
   async def hoy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
       response = await run_agent("Dame el resumen completo de lo que tengo programado para hoy.")
       await update.message.reply_text(response)

   @restricted
   async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
       user_text = update.message.text
       await update.message.chat.send_action("typing")
       response = await run_agent(user_text)
       await update.message.reply_text(response)

   def register_handlers(application):
       application.add_handler(CommandHandler("start", start_command))
       application.add_handler(CommandHandler("hoy", hoy_command))
       application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
   ```

---

## ✅ Verificación de la Tarea
- Arrancar la aplicación y enviar `/start` y `/hoy` desde el chat de Telegram para confirmar respuestas inmediatas.
