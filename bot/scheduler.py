from datetime import date, datetime, timedelta
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import settings
from database.connection import AsyncSessionLocal
from database.crud import (
    get_smart_next_workout_routine, is_pill_taken_today,
    get_or_create_spotify_tracker, update_spotify_last_reminded, get_office_attendance,
    mark_office_night_notified, get_pending_deadline_tasks, get_monthly_workout_summary,
    update_deadline_last_reminded, create_or_get_email_log, mark_email_alert_sent,
    get_unsummarized_emails_for_date, mark_emails_night_summarized
)
from tools.calendar_tools import get_day_events_async, get_week_events_async
from tools.news_weather_tools import get_weather_forecast, get_top_news
from tools.email_tools import get_gmail_service, fetch_unread_emails_metadata
from agent.email_classifier import triage_email

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=timezone(settings.timezone))

def get_today_local() -> date:
    """Devuelve la fecha actual garantizando la zona horaria Europe/Madrid."""
    tz = timezone(settings.timezone)
    return datetime.now(tz).date()

# ---------------------------------------------------------
# CHEQUEO AISLADO Y PERIÓDICO DE DEADLINES PRÓXIMOS
# ---------------------------------------------------------
async def deadline_checker_job(app):
    """
    Comprueba de forma continua e independiente las tareas con fecha límite próximas.
    Envía notificaciones aisladas antes del vencimiento (ej. >24h día sí día no, 24h, 6h, 3h, 1h)
    con un botón táctil [✅ Marcar como hecha]. Al pulsar el botón, se elimina la tarea de PostgreSQL.
    """
    logger.info("Ejecutando job de comprobación periódica aislada de tareas con fecha límite...")
    async with AsyncSessionLocal() as db:
        pending_tasks = await get_pending_deadline_tasks(db)
        now = datetime.now()

        for task in pending_tasks:
            time_left = task.deadline - now
            total_seconds = time_left.total_seconds()
            total_minutes = int(total_seconds / 60)
            total_hours = total_seconds / 3600.0

            should_notify = False
            urgent_level = ""

            if total_seconds <= 0:
                # Tarea vencida
                if not task.last_reminded_at or (now - task.last_reminded_at).total_seconds() >= 3600:
                    should_notify = True
                    urgent_level = "🚨 **¡ATENCIÓN! ESTA TAREA ACABA DE VENCER:**"
            elif total_hours <= 1:
                # Vence en menos de 1 hora -> Recordatorio cada 15 minutos
                if not task.last_reminded_at or (now - task.last_reminded_at).total_seconds() >= 900:
                    should_notify = True
                    urgent_level = f"🔥 **¡URGENTE! Vence en {max(1, total_minutes)} minutos:**"
            elif total_hours <= 3:
                # Vence en menos de 3 horas -> Recordatorio cada 45 minutos
                if not task.last_reminded_at or (now - task.last_reminded_at).total_seconds() >= 2700:
                    should_notify = True
                    urgent_level = f"⚠️ **AVISO PRÓXIMO:** Vence en **{int(total_hours)}h {total_minutes % 60}m**:"
            elif total_hours <= 6:
                # Vence en menos de 6 horas (ej. a las 5 horas) -> Recordatorio cada 2 horas
                if not task.last_reminded_at or (now - task.last_reminded_at).total_seconds() >= 7200:
                    should_notify = True
                    urgent_level = f"⏰ **RECORDATORIO AISLADO:** Faltan **{int(total_hours)}h {total_minutes % 60}m** para el vencimiento:"
            elif total_hours <= 24:
                # Vence en menos de 24 horas -> Recordatorio cada 4 horas
                if not task.last_reminded_at or (now - task.last_reminded_at).total_seconds() >= 14400:
                    should_notify = True
                    urgent_level = f"📅 **RECORDATORIO PRÓXIMO:** Faltan **{int(total_hours)} horas** para la fecha límite:"
            else:
                # Vence en más de 24 horas -> 1 aviso día sí, día no (cada 48 horas / 2 días)
                if not task.last_reminded_at or (now - task.last_reminded_at).total_seconds() >= 172800:
                    should_notify = True
                    days_left = int(total_hours // 24)
                    if days_left == 1:
                        urgent_level = "📌 **RECORDATORIO PENDIENTE:** Falta **1 día** para la fecha límite:"
                    else:
                        urgent_level = f"📌 **RECORDATORIO PENDIENTE:** Faltan **{days_left} días** para la fecha límite:"

            if should_notify:
                keyboard = [[InlineKeyboardButton("✅ Marcar como hecha", callback_data=f"done_deadline_{task.id}")]]
                message_text = (
                    f"{urgent_level}\n\n"
                    f"📌 **{task.title}**\n"
                    f"⏳ Hora límite: **{task.deadline.strftime('%d/%m/%Y a las %H:%M')}**\n\n"
                    f"Haz clic en el botón táctil cuando la hayas completado para eliminarla."
                )
                await update_deadline_last_reminded(db, task.id, now)
                await app.bot.send_message(
                    chat_id=settings.telegram_user_id,
                    text=message_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

def format_fallback_morning_briefing(
    today: date,
    is_monday: bool,
    weather: dict,
    news: list,
    events: list,
    workout,
    deadline_tasks: list,
    pill_taken: bool
) -> str:
    """Genera un briefing matutino estructurado en Python como respaldo garantizado cuando la IA no responde."""
    lines = []

    # 1. El Tiempo
    weather_summary = weather.get("summary", "Sin previsión disponible") if isinstance(weather, dict) else str(weather)
    lines.append(f"🌤️ **El Tiempo hoy**\n{weather_summary}")

    # 2. Noticias
    lines.append("\n📰 **Noticias Destacadas del Día**")
    if news and isinstance(news, list):
        for item in news[:3]:
            source = item.get("source", "Noticia")
            title = item.get("title", "")
            link = item.get("link", "")
            if link:
                lines.append(f"• [{source}]({link}) {title}")
            else:
                lines.append(f"• **{source}:** {title}")
    else:
        lines.append("• No hay noticias disponibles en este momento.")

    # 3. Agenda
    header_cal = "📅 **Agenda completa de esta semana**" if is_monday else "📅 **Agenda de hoy**"
    lines.append(f"\n{header_cal}")
    if events and isinstance(events, list) and not events[0].get("error"):
        for ev in events:
            summary = ev.get("summary", ev.get("title", "Evento"))
            start = ev.get("start", "")
            lines.append(f"• {start} - {summary}".strip(" -"))
    else:
        lines.append("• Sin eventos programados para hoy. ¡Qué aproveche el descanso! 🧘")

    # 4. Tareas con plazo
    lines.append("\n⏳ **Tareas con Plazo Pendientes**")
    if deadline_tasks:
        for dt in deadline_tasks:
            deadline_str = dt.deadline.strftime("%d/%m %H:%M")
            lines.append(f"• {dt.title} 📦 → {deadline_str}")
    else:
        lines.append("• Sin tareas pendientes con fecha límite.")

    # 5. Gimnasio y Pastilla
    workout_str = f"{workout.name} ({workout.target_muscles})" if workout else "Descanso / No definida"
    pill_str = "Ya tomada ✅" if pill_taken else "Pendiente por tomar ⚠️"
    lines.append(f"\n🏋️ **Rutina Sugerida:** {workout_str}")
    lines.append(f"💊 **Estado Pastilla:** {pill_str}")

    return "\n".join(lines)


# ---------------------------------------------------------
# 07:30 AM - BRIEFING MATUTINO Y RECORDATORIO PASTILLA
# ---------------------------------------------------------
async def morning_briefing_job(app):
    logger.info("Ejecutando job de Morning Briefing (07:30 AM)...")
    today = get_today_local()
    is_monday = (today.weekday() == 0)

    weather = await get_weather_forecast()
    news = await get_top_news(3)

    events = []
    try:
        if is_monday:
            events = await get_week_events_async(today)
        else:
            events = await get_day_events_async(today)
    except Exception as e:
        logger.error(f"Error consultando calendario: {e}")
        events = [{"error": str(e)}]

    async with AsyncSessionLocal() as db:
        workout = await get_smart_next_workout_routine(db)
        pill_taken = await is_pill_taken_today(db, target_date=today)
        deadline_tasks = await get_pending_deadline_tasks(db)
    
    summary = format_fallback_morning_briefing(
        today=today,
        is_monday=is_monday,
        weather=weather,
        news=news,
        events=events,
        workout=workout,
        deadline_tasks=deadline_tasks,
        pill_taken=pill_taken
    )

    message_text = f"☀️ **BRIEFING MATUTINO (07:30 AM)**\n\n{summary}"

    keyboard = []
    if not pill_taken:
        keyboard.append([InlineKeyboardButton("💊 Ya me he tomado la pastilla", callback_data="pill_taken")])

    for dt in deadline_tasks:
        keyboard.append([InlineKeyboardButton(f"✅ Marcar hecha: {dt.title[:30]}", callback_data=f"done_deadline_{dt.id}")])

    if today.weekday() == 1:  # Martes
        async with AsyncSessionLocal() as db:
            office_status = await get_office_attendance(db, today + timedelta(days=1))
            if office_status is None:
                message_text += "\n\n🏢 **OFICINA:** ¿Vas a ir a la oficina esta semana?"
                keyboard.append([
                    InlineKeyboardButton("🏢 Sí voy a la oficina", callback_data="office_yes"),
                    InlineKeyboardButton("🏠 No voy (Teletrabajo)", callback_data="office_no")
                ])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await app.bot.send_message(
        chat_id=settings.telegram_user_id,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ---------------------------------------------------------
# 15:00 PM - SEGUNDO AVISO PASTILLA
# ---------------------------------------------------------
async def afternoon_pill_job(app):
    logger.info("Ejecutando job de verificación de pastilla (15:00 PM)...")
    today = get_today_local()
    async with AsyncSessionLocal() as db:
        taken = await is_pill_taken_today(db, target_date=today)
        if not taken:
            keyboard = [[InlineKeyboardButton("💊 Confirmar toma de pastilla", callback_data="pill_taken")]]
            await app.bot.send_message(
                chat_id=settings.telegram_user_id,
                text="💊 **RECORDATORIO (15:00 PM):** Aún no has confirmado la toma de la pastilla de hoy. ¡Por favor tómatela!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

# ---------------------------------------------------------
# 20:00 PM - AVISO GIMNASIO (LUNES A VIERNES)
# ---------------------------------------------------------
async def gym_reminder_job(app):
    today = get_today_local()
    if today.weekday() >= 5:  # Sábado o Domingo: omitir
        return

    logger.info("Ejecutando job de recordatorio de gym (20:00 PM)...")
    async with AsyncSessionLocal() as db:
        workout = await get_smart_next_workout_routine(db)

    if workout:
        text = (
            f"🏋️ **HORA DEL ENTRENAMIENTO (20:00 PM)**\n\n"
            f"La rutina recomendada para hoy es **{workout.name}**\n"
            f"💪 Músculos: {workout.target_muscles}\n"
            f"📋 Ejercicios:\n{workout.description}\n\n"
            f"¡Hora de entrenar!"
        )
    else:
        text = "🏋️ **ENTRENAMIENTO (20:00 PM):** Hoy corresponde día de descanso o actividad libre."

    await app.bot.send_message(
        chat_id=settings.telegram_user_id,
        text=text,
        parse_mode="Markdown"
    )

# ---------------------------------------------------------
# 23:00 PM - NOCHE: PASTILLA, OFICINA, BIZUM DE SPOTIFY, DEADLINES Y RESUMEN MENSUAL
# ---------------------------------------------------------
async def nightly_checks_job(app):
    logger.info("Ejecutando job de chequeos nocturnos (21:00 PM)...")
    today = get_today_local()
    tomorrow = today + timedelta(days=1)

    from bot.handlers import build_spotify_status_and_keyboard

    async with AsyncSessionLocal() as db:
        # 1. Pastilla
        pill_taken = await is_pill_taken_today(db, target_date=today)
        if not pill_taken:
            keyboard = [[InlineKeyboardButton("💊 Confirmar toma de pastilla", callback_data="pill_taken")]]
            await app.bot.send_message(
                chat_id=settings.telegram_user_id,
                text="💊 **ÚLTIMO AVISO PASTILLA (21:00 PM):** No me me has confirmado la toma de la pastilla de hoy.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        # 2. Recordatorio Oficina para mañana
        will_attend_tomorrow = await get_office_attendance(db, tomorrow)
        if will_attend_tomorrow is True:
            await mark_office_night_notified(db, tomorrow)
            await app.bot.send_message(
                chat_id=settings.telegram_user_id,
                text=f"🏢 **RECORDATORIO OFICINA (21:00 PM):** Recuerda que mañana ({tomorrow.strftime('%d/%m/%Y')}) vas a la oficina.",
                parse_mode="Markdown"
            )

        # 3. Bizum de Spotify (A partir del día 16 de cada mes)
        if today.day >= 16:
            tracker = await get_or_create_spotify_tracker(db)
            if not tracker.is_complete:
                should_remind = False
                if not tracker.last_reminded_at:
                    should_remind = True
                else:
                    days_since = (today - tracker.last_reminded_at).days
                    if days_since >= 2:
                        should_remind = True

                if should_remind:
                    text, keyboard = build_spotify_status_and_keyboard(tracker)
                    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                    await update_spotify_last_reminded(db)
                    await app.bot.send_message(
                        chat_id=settings.telegram_user_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )

        # 4. Resumen Mensual de Entrenamientos (Si hoy es el último día del mes)
        is_last_day_of_month = (tomorrow.month != today.month)
        if is_last_day_of_month:
            summary_data = await get_monthly_workout_summary(db, today.year, today.month)
            total = summary_data["total_workouts"]
            breakdown = summary_data["breakdown"]

            breakdown_text = "\n".join([f"• **{name}:** {count} veces" for name, count in breakdown.items()]) if breakdown else "No se registraron entrenamientos este mes."

            msg = (
                f"📊 **RESUMEN MENSUAL DE ENTRENAMIENTOS ({today.strftime('%m/%Y')})**\n\n"
                f"🏆 **Total de sesiones realizadas este mes:** {total}\n\n"
                f"📋 **Desglose por rutina:**\n{breakdown_text}\n\n"
                f"¡Buen trabajo este mes! 💪🔥"
            )
            await app.bot.send_message(
                chat_id=settings.telegram_user_id,
                text=msg,
                parse_mode="Markdown"
            )

        # 5. Resumen Consolidado de Correos del Día (Zero-PII)
        # Sincronización nocturna previa para capturar emails de última hora
        try:
            service = await asyncio.to_thread(get_gmail_service, interactive=False)
            latest_unread = await asyncio.to_thread(fetch_unread_emails_metadata, service, 15, "is:unread")
            if latest_unread:
                for mail_data in latest_unread:
                    msg_id = mail_data.get("message_id")
                    if msg_id:
                        triage_res = await triage_email(mail_data)
                        await create_or_get_email_log(
                            db=db,
                            message_id=msg_id,
                            sender=mail_data.get("sender", ""),
                            subject=mail_data.get("subject", ""),
                            received_at=mail_data.get("received_at") or datetime.now(timezone(settings.timezone)),
                            is_promotional=triage_res.get("is_promotional", False),
                            is_important=triage_res.get("is_important", False)
                        )
        except Exception as sync_err:
            logger.warning(f"Sincronización nocturna de emails omitida o no autenticada: {sync_err}")

        # Consultar correos del día no promocionales pendientes de resumir
        daily_emails = await get_unsummarized_emails_for_date(db, today)
        if daily_emails:
            important_list = [e for e in daily_emails if e.is_important]
            other_list = [e for e in daily_emails if not e.is_important]

            email_lines = []
            if important_list:
                email_lines.append("🔴 **Correos Importantes / Prioritarios:**")
                for e in important_list:
                    sender_clean = e.sender.split("<")[0].strip().strip('"') or e.sender
                    email_lines.append(f"• **{sender_clean}:** {e.subject}")

            if other_list:
                if important_list:
                    email_lines.append("")
                email_lines.append("ℹ️ **Otros correos relevantes del día:**")
                for e in other_list:
                    sender_clean = e.sender.split("<")[0].strip().strip('"') or e.sender
                    email_lines.append(f"• **{sender_clean}:** {e.subject}")

            email_summary_text = "\n".join(email_lines)
            nightly_email_msg = (
                f"📬 **RESUMEN DE CORREOS DEL DÍA ({today.strftime('%d/%m/%Y')})**\n\n"
                f"{email_summary_text}"
            )
            await app.bot.send_message(
                chat_id=settings.telegram_user_id,
                text=nightly_email_msg,
                parse_mode="Markdown"
            )
            await mark_emails_night_summarized(db, [e.id for e in daily_emails])
        else:
            logger.info("Resumen nocturno: no hay correos no promocionales pendientes de resumir para hoy.")

# ---------------------------------------------------------
# MONITOR DIURNO DE CORREOS IMPORTANTES (CADA 15 MINUTOS, 08:00 - 20:45)
# ---------------------------------------------------------
async def daytime_email_monitor_job(app):
    """
    Monitor diurno que inspecciona la bandeja de entrada periódicamente mediante Gmail API
    bajo política Zero-PII, clasifica con IA basada en metadatos y emite alertas push a Telegram.
    """
    logger.info("Ejecutando job de monitor diurno de emails...")
    try:
        service = await asyncio.to_thread(get_gmail_service, interactive=False)
    except Exception as e:
        logger.warning(f"No se pudo inicializar servicio de Gmail (requiere autenticación o credenciales): {e}")
        return

    try:
        unread_emails = await asyncio.to_thread(fetch_unread_emails_metadata, service, 15, "is:unread")
    except Exception as e:
        logger.warning(f"Error al listar emails no leídos de Gmail: {e}")
        return

    if not unread_emails:
        return

    async with AsyncSessionLocal() as db:
        for mail_data in unread_emails:
            msg_id = mail_data.get("message_id")
            if not msg_id:
                continue

            # 1. Triage del correo (Zero-PII: cabeceras locales + LLM metadata-only)
            triage_result = await triage_email(mail_data)
            is_important = triage_result.get("is_important", False)
            is_promotional = triage_result.get("is_promotional", False)
            reason = triage_result.get("reason", "")

            # 2. Registrar en base de datos garantizando idempotencia por message_id
            email_log, created = await create_or_get_email_log(
                db=db,
                message_id=msg_id,
                sender=mail_data.get("sender", ""),
                subject=mail_data.get("subject", ""),
                received_at=mail_data.get("received_at") or datetime.now(timezone(settings.timezone)),
                is_promotional=is_promotional,
                is_important=is_important
            )

            # 3. Si es importante y aún no se ha alertado, emitir notificación enriquecida en Telegram
            if email_log.is_important and not email_log.alert_sent and not email_log.is_promotional:
                gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{email_log.message_id}"
                keyboard = [[InlineKeyboardButton("📬 Abrir en Gmail", url=gmail_url)]]

                alert_text = (
                    f"🚨 **CORREO IMPORTANTE DETECTADO**\n\n"
                    f"👤 **De:** {email_log.sender}\n"
                    f"📌 **Asunto:** {email_log.subject}\n"
                    f"💡 **Motivo:** {reason}"
                )

                try:
                    await app.bot.send_message(
                        chat_id=settings.telegram_user_id,
                        text=alert_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                    await mark_email_alert_sent(db, email_log.id)
                    logger.info(f"Alerta enviada para email {email_log.message_id} de {email_log.sender}")
                except Exception as send_err:
                    logger.error(f"Error al enviar mensaje de alerta Telegram para email {email_log.id}: {send_err}")


# ---------------------------------------------------------
# 22:00 PM - CHECK-IN GIMNASIO (LUNES A VIERNES)
# ---------------------------------------------------------
async def nightly_gym_checkin_job(app):
    today = get_today_local()
    if today.weekday() >= 5:  # Sábado o Domingo: omitir
        return

    logger.info("Ejecutando job de Check-in Gym Nocturno (22:00 PM)...")
    keyboard = [
        [InlineKeyboardButton("✅ Entreno Hecho", callback_data="workout_done")],
        [InlineKeyboardButton("🧗 Fui a Escalada", callback_data="workout_climbing")],
        [InlineKeyboardButton("💤 Día de Descanso", callback_data="workout_rest")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await app.bot.send_message(
        chat_id=settings.telegram_user_id,
        text="🌙 **CHECK-IN ENTRENAMIENTO (22:00 PM)**\n¿Cómo ha ido la sesión de hoy?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ---------------------------------------------------------
# START SCHEDULER WITH ALL CRON JOBS
# ---------------------------------------------------------
def start_scheduler(app):
    # 0. Chequeo periódico aislado de deadlines cada 15 minutos
    scheduler.add_job(
        deadline_checker_job,
        'interval',
        minutes=15,
        args=[app],
        id="deadline_checker"
    )

    # 1. Briefing matutino + Pastilla + Agenda semanal (Lunes 07:30) / diaria (07:30)
    scheduler.add_job(
        morning_briefing_job,
        'cron',
        hour=7,
        minute=30,
        args=[app],
        id="morning_briefing"
    )

    # 2. Segundo aviso pastilla (15:00 PM)
    scheduler.add_job(
        afternoon_pill_job,
        'cron',
        hour=15,
        minute=0,
        args=[app],
        id="afternoon_pill"
    )

    # 3. Aviso Gimnasio (20:00 PM Lunes a Viernes)
    scheduler.add_job(
        gym_reminder_job,
        'cron',
        hour=20,
        minute=0,
        args=[app],
        id="gym_reminder"
    )

    # 4. Chequeos nocturnos: Pastilla 3er aviso + Oficina + Bizum Spotify + Resumen Mensual (23:00 PM)
    scheduler.add_job(
        nightly_checks_job,
        'cron',
        hour=23,
        minute=0,
        args=[app],
        id="nightly_checks"
    )

    # 5. Check-in Gimnasio (22:00 PM Lunes a Viernes)
    scheduler.add_job(
        nightly_gym_checkin_job,
        'cron',
        hour=22,
        minute=0,
        args=[app],
        id="nightly_gym_checkin"
    )

    # 6. Monitor diurno de correos importantes (Cada 15 min entre 08:00 y 20:45)
    scheduler.add_job(
        daytime_email_monitor_job,
        'cron',
        hour='8-20',
        minute='*/15',
        args=[app],
        id="daytime_email_monitor"
    )

    scheduler.start()
    logger.info("AsyncIOScheduler iniciado con éxito con comprobador de deadlines (cada 15m), monitor de email y crons en " + settings.timezone)
