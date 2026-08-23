# 🔹 Tarea 6.4 — Sistema de Logs y Alertas de Fallos en Telegram

## 🎯 Objetivo
Configurar el sistema de registro de eventos (*logging*) con rotación de ficheros y un gestor global de excepciones que notifique cualquier fallo crítico directamente al chat del desarrollador en Telegram.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Configurar Logging Rotativo (`config/logging_config.py`):**
   ```python
   import logging
   from logging.handlers import RotatingFileHandler
   import os

   def setup_logging():
       os.makedirs("logs", exist_ok=True)
       logger = logging.getLogger()
       logger.setLevel(logging.INFO)

       formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

       file_handler = RotatingFileHandler("logs/app.log", maxBytes=5*1024*1024, backupCount=3)
       file_handler.setFormatter(formatter)
       logger.addHandler(file_handler)

       console_handler = logging.StreamHandler()
       console_handler.setFormatter(formatter)
       logger.addHandler(console_handler)
   ```

2. **Implementar Error Handler Global en Telegram (`bot/handlers.py`):**
   ```python
   import traceback
   import html
   from telegram import Update
   from telegram.ext import ContextTypes
   from config.settings import settings

   async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
       logging.error("Excepción no capturada manejando un update:", exc_info=context.error)
       
       tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
       tb_string = "".join(tb_list)
       
       message = (
           "🚨 **ALERTA DE ERROR EN EL BOT** 🚨\n\n"
           f"<code>{html.escape(tb_string[-3000:])}</code>"
       )
       
       try:
           await context.bot.send_message(
               chat_id=settings.telegram_user_id,
               text=message,
               parse_mode="HTML"
           )
       except Exception as e:
           logging.error(f"No se pudo enviar la alerta de error por Telegram: {e}")
   ```

---

## ✅ Verificación de la Tarea
- Provocar deliberadamente una excepción en un comando de prueba y verificar que se genere la entrada en `logs/app.log` y que llegue el mensaje con el traceback al Telegram del usuario.
