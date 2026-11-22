from functools import wraps
import logging
from datetime import datetime, date, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.settings import settings
from agent.engine import run_agent
from database.connection import AsyncSessionLocal
from database.crud import (
    get_smart_next_workout_routine, log_completed_workout, get_due_recurring_tasks,
    mark_task_completed, confirm_pill_taken, is_pill_taken_today, set_office_attendance,
    get_or_create_spotify_tracker, update_spotify_friend_payment, log_activity_by_name,
    get_pending_deadline_tasks, mark_deadline_task_completed, get_week_office_dates,
    clear_office_attendance, mark_email_user_corrected
)
from tools.calendar_tools import get_day_events_async
from tools.news_weather_tools import get_weather_forecast, get_top_news

logger = logging.getLogger(__name__)

DIAS_SEMANA_ES = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

def get_today_local() -> date:
    """Devuelve la fecha actual garantizando la zona horaria Europe/Madrid."""
    tz = pytz.timezone(settings.timezone)
    return datetime.now(tz).date()

async def safe_send_typing(chat):
    """Envía la acción 'typing' atrapando posibles timeouts o micro-cortes de red de Telegram."""
    if not chat:
        return
    try:
        await chat.send_action("typing")
    except Exception as e:
        logger.warning(f"No se pudo enviar el indicador 'typing' a Telegram por timeout/red: {e}")

async def safe_reply_text(message, text: str, reply_markup=None):
    """Envía un mensaje intentando formato Markdown, con fallback a texto plano si falla el parseo o el texto es vacío."""
    if not text or not text.strip():
        text = "📅 Información procesada correctamente."

    try:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Error enviando mensaje con parse_mode Markdown: {e}. Reintentando sin formato...")
        try:
            await message.reply_text(text, reply_markup=reply_markup)
        except Exception as e2:
            logger.error(f"Error definitivo enviando mensaje de texto: {e2}")

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id != settings.telegram_user_id:
            logger.warning(f"[SECURITY] Acceso denegado a usuario no autorizado: {user_id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador global para capturar errores de red (como TimedOut / ConnectTimeout) y evitar caídas del proceso."""
    logger.warning(f"Excepción de red/sistema capturada en Telegram handler: {context.error}")
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Hubo un micro-corte temporal de red con Telegram. Por favor, reintenta tu comando."
            )
        except Exception:
            pass

def build_spotify_status_and_keyboard(tracker) -> tuple[str, list]:
    """Genera el texto de estado del Bizum de Spotify y botones SOLO para los amigos pendientes."""
    status_ruben = "✅ Pagado" if tracker.ruben_paid else "❌ Pendiente"
    status_vic = "✅ Pagado" if tracker.victoriano_paid else "❌ Pendiente"
    status_miquel = "✅ Pagado" if tracker.miquel_paid else "❌ Pendiente"
    status_joan = "✅ Pagado" if tracker.joan_paid else "❌ Pendiente"

    text = (
        f"🎵 **CONTROL BIZUM SPOTIFY ({tracker.month_key})**\n\n"
        f"👥 **Estado de pagos de este mes ({tracker.paid_count}/4):**\n"
        f"• **Ruben:** {status_ruben}\n"
        f"• **Victoriano:** {status_vic}\n"
        f"• **Miquel:** {status_miquel}\n"
        f"• **Joan:** {status_joan}\n"
    )

    if tracker.is_complete:
        text += "\n🎉 **¡Todos tus amigos (Ruben, Victoriano, Miquel y Joan) te han pagado el Spotify este mes!**"
    else:
        rem = tracker.total_friends - tracker.paid_count
        text += f"\n⚠️ **Faltan {rem} amigo(s) por pagarte.** Haz clic abajo para registrar el pago:"

    keyboard = []
    row1 = []
    if not tracker.ruben_paid:
        row1.append(InlineKeyboardButton("💵 Ruben pagó", callback_data="spotify_paid_ruben"))
    if not tracker.victoriano_paid:
        row1.append(InlineKeyboardButton("💵 Victoriano pagó", callback_data="spotify_paid_victoriano"))
    if row1:
        keyboard.append(row1)

    row2 = []
    if not tracker.miquel_paid:
        row2.append(InlineKeyboardButton("💵 Miquel pagó", callback_data="spotify_paid_miquel"))
    if not tracker.joan_paid:
        row2.append(InlineKeyboardButton("💵 Joan pagó", callback_data="spotify_paid_joan"))
    if row2:
        keyboard.append(row2)

    return text, keyboard


def format_fallback_hoy_summary(
    today: date,
    day_es: str,
    weather: dict,
    news: list,
    events: list,
    deadline_tasks: list
) -> str:
    """Genera un resumen diario estructurado en Python como respaldo garantizado para /hoy."""
    lines = []

    # 1. El Tiempo
    weather_summary = weather.get("summary", "Sin previsión disponible") if isinstance(weather, dict) else str(weather)
    lines.append(f"🌤️ **El Tiempo hoy ({day_es} {today.strftime('%d/%m/%Y')})**\n{weather_summary}")

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
    lines.append("\n📅 **Agenda**")
    if events and isinstance(events, list) and not events[0].get("error"):
        for ev in events:
            summary = ev.get("summary", ev.get("title", "Evento"))
            start = ev.get("start", "")
            lines.append(f"• {start} - {summary}".strip(" -"))
    else:
        lines.append("• Sin eventos programados para hoy. ¡Qué aproveche el descanso! 🧘")

    # 4. Tareas con plazo
    lines.append("\n⏳ **Tareas con Plazo**")
    if deadline_tasks:
        for dt in deadline_tasks:
            deadline_str = dt.deadline.strftime("%d/%m %H:%M")
            lines.append(f"• {dt.title} 📦 → {deadline_str}")
    else:
        lines.append("• Sin tareas pendientes con fecha límite.")

    return "\n".join(lines)


async def generate_hoy_summary() -> tuple[str, list]:
    """Pre-recopila únicamente Weather, Noticias, Calendar y Deadlines para generar /hoy limpio sin incluir pastilla, gimnasio ni spotify."""
    today = get_today_local()
    tz = pytz.timezone(settings.timezone)
    now = datetime.now(tz)
    day_es = DIAS_SEMANA_ES.get(now.strftime("%A"), now.strftime("%A"))
    
    weather = await get_weather_forecast()
    news = await get_top_news(3)

    try:
        events = await get_day_events_async(today)
    except Exception as e:
        logger.error(f"Error consultando calendario en /hoy: {e}")
        events = [{"error": str(e)}]

    async with AsyncSessionLocal() as db:
        deadline_tasks = await get_pending_deadline_tasks(db)

    prompt = f"""
Genera un resumen diario conciso, visual, claro, amigable y muy estructurado con emojis en castellano para David:
- Día de hoy: {day_es} {today.strftime('%d/%m/%Y')}
- Previsión del Tiempo: {weather['summary']}
- Noticias destacadas del día:
{[{'source': item['source'], 'title': item['title']} for item in news]}
- Agenda de Google Calendar para hoy: {events}
- Tareas pendientes con fecha límite: {[{'id': t.id, 'title': t.title, 'deadline': t.deadline.strftime('%d/%m %H:%M')} for t in deadline_tasks]}

Instrucciones de formato estricto:
- Incluye ÚNICAMENTE las siguientes 4 secciones estructuradas con emojis:
  1. 🌤️ **El Tiempo hoy**
  2. 📰 **Noticias Destacadas del Día**
  3. 📅 **Agenda**
  4. ⏳ **Tareas con Plazo**
- NO incluyas ninguna sección sobre el estado de la pastilla, el gimnasio ni el Spotify en este resumen /hoy.
- Muestra los titulares de las 2-3 noticias principales.
- No muestres pensamientos internos, razonamientos ni planificación.
"""

    response = None
    try:
        res = await run_agent(prompt, enable_tools=False)
        if res and res.strip() and not res.strip().startswith("⚠️"):
            response = res
    except Exception as err:
        logger.warning(f"Error generando /hoy con IA: {err}")

    if not response:
        logger.info("Usando plantilla determinista de respaldo en Python para /hoy.")
        response = format_fallback_hoy_summary(
            today=today,
            day_es=day_es,
            weather=weather,
            news=news,
            events=events,
            deadline_tasks=deadline_tasks
        )

    keyboard = []
    for dt in deadline_tasks:
        keyboard.append([InlineKeyboardButton(f"✅ Marcar hecha: {dt.title[:30]}", callback_data=f"done_deadline_{dt.id}")])

    return response, keyboard


@restricted
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **¡Hola! Soy Jarvis**, el asistente personal inteligente de David.\n\n"
        "Puedo ayudarte a:\n"
        "🌤️ Consultar **el tiempo y las 2-3 noticias del día**\n"
        "📅 Gestionar tus eventos en **Google Calendar**\n"
        "💊 Recordar y consultar la **toma de tu pastilla** (`/pastilla`)\n"
        "🏋️ Sugerir rutinas de gym adaptativas (**Push/Pull/Pierna/Full-Body/Descanso**)\n"
        "🎵 Controlar el cobro de **Spotify Bizum** a Ruben, Victoriano, Miquel y Joan (`/spotify`)\n"
        "🏢 Planificar la **asistencia a la oficina**\n"
        "⏳ Recordar y gestionar **tareas con plazo límite (deadlines)**\n\n"
        "💡 *Comandos disponibles:*\n"
        "• `/hoy` — Tiempo, noticias, agenda y tareas con plazo\n"
        "• `/pastilla` — Consultar estado de la pastilla de hoy\n"
        "• `/spotify` — Estado y botones de Bizum de Spotify\n"
        "• `/entreno` — Consultar qué entreno toca hoy\n"
        "• O escríbeme lo que necesites en lenguaje natural."
    )
    
    today = get_today_local()
    async with AsyncSessionLocal() as db:
        pill_taken = await is_pill_taken_today(db, target_date=today)
        deadline_tasks = await get_pending_deadline_tasks(db)

    keyboard = [
        [
            InlineKeyboardButton("📅 Agenda de Hoy", callback_data="btn_hoy"),
            InlineKeyboardButton("🏋️ Ver Entreno", callback_data="btn_entreno"),
            InlineKeyboardButton("🎵 Spotify Bizum", callback_data="btn_spotify")
        ]
    ]

    if not pill_taken:
        keyboard.append([InlineKeyboardButton("💊 Confirmar Pastilla", callback_data="pill_taken")])

    for dt in deadline_tasks:
        keyboard.append([InlineKeyboardButton(f"✅ Marcar hecha: {dt.title[:30]}", callback_data=f"done_deadline_{dt.id}")])

    await safe_reply_text(update.message, welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

@restricted
async def hoy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send_typing(update.message.chat)
    response, keyboard = await generate_hoy_summary()
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await safe_reply_text(update.message, response, reply_markup=reply_markup)

@restricted
async def pastilla_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send_typing(update.message.chat)
    today = get_today_local()
    async with AsyncSessionLocal() as db:
        taken = await is_pill_taken_today(db, target_date=today)
    
    if taken:
        text = (
            f"💊 **ESTADO DE LA PASTILLA ({today.strftime('%d/%m/%Y')})**\n\n"
            f"✅ **¡Ya te has tomado la pastilla de hoy!** Todo en orden."
        )
        await safe_reply_text(update.message, text)
    else:
        text = (
            f"💊 **ESTADO DE LA PASTILLA ({today.strftime('%d/%m/%Y')})**\n\n"
            f"⚠️ **Aún no has confirmado la pastilla de hoy.**\n"
            f"¡Por favor tómatela cuanto antes!"
        )
        keyboard = [[InlineKeyboardButton("💊 Confirmar Pastilla de hoy", callback_data="pill_taken")]]
        await safe_reply_text(update.message, text, reply_markup=InlineKeyboardMarkup(keyboard))

@restricted
async def spotify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send_typing(update.message.chat)
    async with AsyncSessionLocal() as db:
        tracker = await get_or_create_spotify_tracker(db)
        text, keyboard = build_spotify_status_and_keyboard(tracker)
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await safe_reply_text(update.message, text, reply_markup=reply_markup)

@restricted
async def entreno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_send_typing(update.message.chat)
    response = await run_agent("¿Qué rutina de gimnasio me toca entrenar hoy?")
    keyboard = [
        [InlineKeyboardButton("✅ Entreno Hecho", callback_data="workout_done")],
        [InlineKeyboardButton("🧗 Fui a Escalada", callback_data="workout_climbing")],
        [InlineKeyboardButton("💤 Día de Descanso", callback_data="workout_rest")]
    ]
    await safe_reply_text(update.message, response, reply_markup=InlineKeyboardMarkup(keyboard))

@restricted
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await safe_send_typing(update.message.chat)
    response = await run_agent(user_text)
    await safe_reply_text(update.message, response)

@restricted
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Callback recibido: {data}")
    today = get_today_local()

    async with AsyncSessionLocal() as db:
        if data == "btn_hoy":
            await safe_send_typing(query.message.chat)
            response, keyboard = await generate_hoy_summary()
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await safe_reply_text(query.message, response, reply_markup=reply_markup)

        elif data == "btn_spotify":
            await safe_send_typing(query.message.chat)
            tracker = await get_or_create_spotify_tracker(db)
            text, keyboard = build_spotify_status_and_keyboard(tracker)
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await safe_reply_text(query.message, text, reply_markup=reply_markup)

        elif data == "btn_entreno":
            await safe_send_typing(query.message.chat)
            response = await run_agent("¿Qué rutina de gimnasio me toca entrenar hoy?")
            keyboard = [
                [InlineKeyboardButton("✅ Entreno Hecho", callback_data="workout_done")],
                [InlineKeyboardButton("🧗 Fui a Escalada", callback_data="workout_climbing")],
                [InlineKeyboardButton("💤 Día de Descanso", callback_data="workout_rest")]
            ]
            await safe_reply_text(query.message, response, reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("done_deadline_"):
            task_id = int(data.split("done_deadline_")[1])
            task = await mark_deadline_task_completed(db, task_id)
            if task:
                await query.edit_message_text(f"✅ **Tarea Completada y Eliminada:** '{task.title}'", parse_mode="Markdown")
            else:
                await query.edit_message_text(f"⚠️ La tarea ID {task_id} ya fue completada o eliminada previamente.")

        elif data == "pill_taken":
            entry = await confirm_pill_taken(db, target_date=today)
            await query.edit_message_text(f"💊 **¡Pastilla Confirmada!** Registrada como tomada hoy {entry.log_date}. ¡Gracias!", parse_mode="Markdown")

        elif data.startswith("spotify_paid_"):
            friend_name = data.split("spotify_paid_")[1]
            tracker = await update_spotify_friend_payment(db, friend_name, True)
            text, keyboard = build_spotify_status_and_keyboard(tracker)
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

        elif data == "workout_done":
            workout = await get_smart_next_workout_routine(db)
            if workout:
                log_entry = await log_completed_workout(db, workout_id=workout.id, notes="Completado vía botón inline")
                await query.edit_message_text(
                    f"💪 **¡Entrenamiento Registrado!**\n\n"
                    f"Se ha completado la rutina **{workout.name}** ({workout.target_muscles}). ¡Excelente trabajo! 🔥",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("⚠️ No se encontró rutina activa para registrar.")

        elif data == "workout_climbing":
            await log_activity_by_name(db, "Escalada", notes="Registrado vía botón inline")
            await query.edit_message_text("🧗 **¡Sesión de Escalada Registrada!** Mañana ajustaremos la rotación para no cargar la espalda (se omitirá Pull).", parse_mode="Markdown")

        elif data == "workout_rest":
            await log_activity_by_name(db, "Descanso", notes="Registrado vía botón inline")
            await query.edit_message_text("💤 **Día de Descanso Registrado**\n¡A recuperar energías! La rotación de tu entrenamiento se mantendrá lista para tu próxima sesión.", parse_mode="Markdown")

        elif data == "office_day_thu":
            thursday, friday = get_week_office_dates(today)
            await set_office_attendance(db, thursday, True)
            await set_office_attendance(db, friday, False)
            await query.edit_message_text(
                f"🏢 **Oficina Confirmada:** Registrado que irás a la oficina el **Jueves {thursday.strftime('%d/%m/%Y')}**.\n"
                f"Te lo recordaré el miércoles por la noche (23:00 PM).",
                parse_mode="Markdown"
            )

        elif data == "office_day_fri":
            thursday, friday = get_week_office_dates(today)
            await set_office_attendance(db, thursday, False)
            await set_office_attendance(db, friday, True)
            await query.edit_message_text(
                f"🏢 **Oficina Confirmada:** Registrado que irás a la oficina el **Viernes {friday.strftime('%d/%m/%Y')}**.\n"
                f"Te lo recordaré el jueves por la noche (23:00 PM).",
                parse_mode="Markdown"
            )

        elif data == "office_day_none":
            thursday, friday = get_week_office_dates(today)
            await set_office_attendance(db, thursday, False)
            await set_office_attendance(db, friday, False)
            await query.edit_message_text(
                "🏠 Registrado que te quedas en casa toda esta semana (teletrabajo). No habrá avisos de oficina.",
                parse_mode="Markdown"
            )

        elif data == "office_day_unknown":
            thursday, friday = get_week_office_dates(today)
            await clear_office_attendance(db, thursday)
            await clear_office_attendance(db, friday)
            await query.edit_message_text(
                "❓ Entendido, aún no lo sabes con seguridad. Te volveré a preguntar mañana.",
                parse_mode="Markdown"
            )

        elif data == "office_yes":
            target_dt = today + timedelta(days=1)
            await set_office_attendance(db, target_dt, True)
            await query.edit_message_text(f"🏢 **Oficina Confirmada**: Registrado que irás a la oficina el {target_dt.strftime('%d/%m/%Y')}. Te lo recordaré la noche anterior a las 23:00 PM.", parse_mode="Markdown")

        elif data == "office_no":
            target_dt = today + timedelta(days=1)
            await set_office_attendance(db, target_dt, False)
            await query.edit_message_text(f"🏠 Registrado que te quedas en casa el {target_dt.strftime('%d/%m/%Y')}.", parse_mode="Markdown")

        elif data == "tasks_done":
            due_tasks = await get_due_recurring_tasks(db)
            if due_tasks:
                completed_names = []
                for t in due_tasks:
                    await mark_task_completed(db, t.id)
                    completed_names.append(t.title)
                await query.edit_message_text(
                    f"🧹 **Tareas del Hogar Marcadas como Completadas**\n\n"
                    + "\n".join([f"✓ {name}" for name in completed_names]),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("✨ ¡No tenías tareas pendientes vencidas hoy! Todo al día.", parse_mode="Markdown")

        elif data.startswith("email_not_important_"):
            # Bucle de aprendizaje: usuario indica que el email NO era importante
            email_log_id = int(data.split("email_not_important_")[1])
            updated = await mark_email_user_corrected(db, email_log_id, was_important=False)
            if updated:
                await query.edit_message_text(
                    f"✅ **Corrección registrada:** El correo de *{updated.sender.split('<')[0].strip()}* "
                    f"ha sido marcado como **no importante**. Aprenderé de esta corrección para mejorar las próximas clasificaciones.",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("⚠️ No se encontró el correo para corregir. Es posible que ya haya sido procesado.")

def register_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("hoy", hoy_command))
    application.add_handler(CommandHandler("pastilla", pastilla_command))
    application.add_handler(CommandHandler("spotify", spotify_command))
    application.add_handler(CommandHandler("entreno", entreno_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    application.add_error_handler(global_error_handler)
