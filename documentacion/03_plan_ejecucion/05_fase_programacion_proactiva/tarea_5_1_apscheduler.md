# 🔹 Tarea 5.1 — Integración de APScheduler en el Ciclo de Eventos

## 🎯 Objetivo
Inicializar `AsyncIOScheduler` dentro del proceso de arranque del bot de Telegram, asegurando que comparta el mismo ciclo de eventos asíncrono (`asyncio event loop`).

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar `bot/scheduler.py`:**
   ```python
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   from pytz import timezone
   from config.settings import settings

   scheduler = AsyncIOScheduler(timezone=timezone(settings.timezone))

   def start_scheduler(app):
       # Registra los crons de briefing y checkin pasando la instancia de Telegram app
       scheduler.add_job(
           morning_briefing_job,
           'cron',
           hour=8,
           minute=0,
           args=[app]
       )
       scheduler.add_job(
           nightly_checkin_job,
           'cron',
           hour=21,
           minute=30,
           args=[app]
       )
       scheduler.start()
   ```

---

## ✅ Verificación de la Tarea
- Arrancar el bot y verificar en consola la salida del log indicando que el scheduler inició sin lanzar excepciones de bucle de eventos.
