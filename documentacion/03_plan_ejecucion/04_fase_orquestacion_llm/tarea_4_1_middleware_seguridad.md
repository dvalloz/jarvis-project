# 🔹 Tarea 4.1 — Middleware de Autorización y Seguridad (`bot/handlers.py`)

## 🎯 Objetivo
Garantizar la privacidad del bot rechazando silenciosamente cualquier interacción de usuarios no autorizados a nivel de middleware.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear Decorador de Seguridad:**
   ```python
   from functools import wraps
   from telegram import Update
   from telegram.ext import ContextTypes
   from config.settings import settings

   def restricted(func):
       @wraps(func)
       async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
           user_id = update.effective_user.id if update.effective_user else None
           if user_id != settings.telegram_user_id:
               print(f"[SECURITY] Acceso denegado a usuario no autorizado: {user_id}")
               return
           return await func(update, context, *args, **kwargs)
       return wrapped
   ```

---

## ✅ Verificación de la Tarea
- Enviar un mensaje desde una cuenta secundaria de Telegram y verificar en los logs que el mensaje sea descartado silenciosamente.
