# 📍 Fase 5: Programación Proactiva y Mensajería Automática (Resumen de Fase)

Esta fase implementa la proactividad del sistema mediante `APScheduler` para el envío automático del Briefing Matutino (08:00 AM) y el Check-in Nocturno Interactivo (21:30 PM) con Inline Keyboards.

---

## 📂 Documentos de Tarea Incluidos

1. 🔹 [Tarea 5.1 — Integración de APScheduler en el Ciclo de Eventos](./tarea_5_1_apscheduler.md)
2. 🔹 [Tarea 5.2 — Implementación del Briefing Matutino (Cron: 08:00 AM)](./tarea_5_2_briefing_matutino.md)
3. 🔹 [Tarea 5.3 — Implementación del Check-in Nocturno (Cron: 21:30 PM)](./tarea_5_3_checkin_nocturno.md)
4. 🔹 [Tarea 5.4 — Manejador de Respuestas de Teclado (`CallbackQueryHandler`)](./tarea_5_4_callback_keyboards.md)

---

## 🎯 Entregables Globales de la Fase

* Instancia de `AsyncIOScheduler` operando dentro del event loop de Telegram.
* Tarea cron matutina (08:00 AM) enviando resumen sintetizado por el LLM.
* Tarea cron nocturna (21:30 PM) con teclado interactivo de tres opciones.
* Manejador `CallbackQueryHandler` procesando registros directamente en PostgreSQL.
