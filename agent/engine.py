import json
import re
import logging
from openai import AsyncOpenAI
from config.settings import settings
from tools.registry import TOOLS_SCHEMA
from tools.news_weather_tools import get_top_news, get_weather_forecast
from tools.calendar_tools import get_day_events, get_week_events, create_calendar_event
from tools.workout_tools import (
    get_next_workout_tool,
    log_climbing_tool,
    log_rest_day_tool,
    get_monthly_workout_summary_tool
)
from tools.task_tools import (
    confirm_pill_tool,
    check_pill_status_tool,
    update_spotify_tool,
    update_spotify_friend_tool,
    set_office_tool,
    add_deadline_tool,
    get_pending_deadline_tasks_tool,
    mark_deadline_task_completed_tool,
    delete_deadline_task_tool,
    update_deadline_task_tool
)
from agent.prompts import get_system_prompt

logger = logging.getLogger(__name__)

# Configuración de Groq API con fallback dinámico de modelos si hay Rate Limit 429
is_groq = settings.groq_api_key and settings.groq_api_key.startswith("gsk_")

if is_groq:
    logger.info("Usando motor Groq API con fallback multimodelo (Qwen 27B / GPT-OSS 120B / GPT-OSS 20B)...")
    client = AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    MODELS_TO_TRY = ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
else:
    logger.info("Usando motor OpenAI API (gpt-4o-mini)...")
    client = AsyncOpenAI(
        api_key=settings.openai_api_key
    )
    MODELS_TO_TRY = ["gpt-4o-mini"]

def clean_think_tags(text: str) -> str:
    """Elimina etiquetas de razonamiento interno (<think>) y monólogos de planificación de forma segura."""
    if not text or not text.strip():
        logger.warning("clean_think_tags: El texto recibido de la IA está vacío o nulo.")
        return "📅 Resumen procesado correctamente."

    # 1. Eliminar bloques <tool_call>...</tool_call>
    cleaned = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL).strip()
    if not cleaned:
        logger.warning("clean_think_tags: El texto solo contenía bloques <tool_call> y quedó vacío.")
        return "📅 Resumen procesado correctamente."

    # 2. Si no hay <think>, devolver directamente
    if "<think>" not in cleaned:
        return cleaned.strip()

    # 3. Intentar quitar <think>...</think> si hay texto fuera
    without_think = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL).strip()
    if without_think:
        return without_think

    # 4. Si todo el texto está dentro de <think>, extraer el contenido
    inside_match = re.search(r'<think>(.*?)</think>', cleaned, flags=re.DOTALL)
    inside_text = inside_match.group(1).strip() if inside_match else cleaned

    # Buscar la primera ocurrencia de un saludo, emoji típico o sección formateada
    pattern = r'(\n(?:👋|🌤️|📰|📅|💊|⏳|🏋️|🎵|\*\*|#|👥|⚠️).*)$'
    match = re.search(pattern, inside_text, flags=re.DOTALL)

    if match:
        result = match.group(1).strip()
        if result.endswith("Perfect."):
            result = result[:-8].strip()
        return result

    # Si no se encuentra patrón, buscar líneas que no parezcan monólogo técnico
    lines = inside_text.split('\n')
    filtered_lines = []
    in_draft = False

    for line in lines:
        l_str = line.strip()
        if not in_draft:
            if l_str.startswith(("Here's a thinking", "1.", "2.", "3.", "4.", "5.", "- **", "Analyze User Input", "Draft:", "Structure:", "El usuario quiere", "Pasos siguientes:")):
                continue
            if l_str and not l_str.startswith(("Here", "Analyze", "Refine", "Check", "Draft", "Structure")):
                in_draft = True
                filtered_lines.append(line)
        else:
            filtered_lines.append(line)

    final_result = "\n".join(filtered_lines).strip()
    if final_result.endswith("Perfect."):
        final_result = final_result[:-8].strip()

    return final_result if final_result else inside_text

def parse_xml_tool_calls(content: str):
    """
    Parsea llamadas a herramientas emitidas en formato XML por algunos modelos open-weights
    cuando las generan como texto plano en lugar de la propiedad nativa tool_calls.
    """
    if not content or "<tool_call>" not in content:
        return []

    calls = []
    blocks = re.findall(r'<tool_call>(.*?)</tool_call>', content, flags=re.DOTALL)
    for block in blocks:
        func_match = re.search(r'<function=(.*?)>', block)
        if not func_match:
            continue
        func_name = func_match.group(1).strip()
        
        params = {}
        param_matches = re.findall(r'<parameter=(.*?)>(.*?)</parameter>', block, flags=re.DOTALL)
        for p_name, p_val in param_matches:
            p_name = p_name.strip()
            p_val = p_val.strip()
            if "~" in p_val:
                p_val = p_val.split("~")[0].strip()
            params[p_name] = p_val

        calls.append({"name": func_name, "args": params})
    return calls

async def execute_tool_call(function_name: str, args: dict) -> str:
    """Ejecuta la función correspondiente según el nombre de la herramienta."""
    logger.info(f"Ejecutando tool '{function_name}' con argumentos: {args}")
    
    # Limpieza de fechas si se pasa rango con tilde ~
    if "date_str" in args and isinstance(args["date_str"], str) and "~" in args["date_str"]:
        args["date_str"] = args["date_str"].split("~")[0].strip()

    if function_name == "get_calendar_events":
        date_str = args.get("date_str")
        events = get_day_events(date_str)
        return json.dumps(events, ensure_ascii=False)

    elif function_name == "get_weekly_calendar_events":
        date_str = args.get("date_str")
        events = get_week_events(date_str)
        return json.dumps(events, ensure_ascii=False)

    elif function_name == "create_calendar_event":
        summary = args.get("summary")
        start_iso = args.get("start_iso")
        end_iso = args.get("end_iso")
        description = args.get("description", "")
        link = create_calendar_event(summary, start_iso, end_iso, description)
        return f"Evento creado con éxito en Google Calendar. Enlace: {link}"

    elif function_name == "get_next_workout":
        return await get_next_workout_tool()

    elif function_name == "get_monthly_workout_summary":
        year = args.get("year")
        month = args.get("month")
        summary_data = await get_monthly_workout_summary_tool(year, month)
        return json.dumps(summary_data, ensure_ascii=False)

    elif function_name == "confirm_pill_taken":
        return await confirm_pill_tool()

    elif function_name == "check_pill_status":
        return await check_pill_status_tool()

    elif function_name == "update_spotify_bizum":
        paid_count = int(args.get("paid_count", 0))
        return await update_spotify_tool(paid_count)

    elif function_name == "update_spotify_friend_payment":
        friend_name = args.get("friend_name", "")
        is_paid = args.get("is_paid", True)
        if isinstance(is_paid, str):
            is_paid = is_paid.lower() in ("true", "1")
        return await update_spotify_friend_tool(friend_name, is_paid)

    elif function_name == "set_office_attendance":
        date_str = args.get("date_str")
        will_attend = True
        if "will_attend" in args:
            w_val = args["will_attend"]
            will_attend = (w_val is True) or (isinstance(w_val, str) and w_val.lower() in ("true", "1"))
        return await set_office_tool(date_str, will_attend)

    elif function_name == "add_deadline_task":
        title = args.get("title")
        deadline_iso = args.get("deadline_iso")
        return await add_deadline_tool(title, deadline_iso)

    elif function_name == "get_pending_deadline_tasks":
        return await get_pending_deadline_tasks_tool()

    elif function_name == "mark_deadline_task_completed":
        task_id = int(args.get("task_id", 0))
        return await mark_deadline_task_completed_tool(task_id)

    elif function_name == "delete_deadline_task":
        task_id = int(args.get("task_id", 0))
        return await delete_deadline_task_tool(task_id)

    elif function_name == "update_deadline_task":
        task_id = int(args.get("task_id", 0))
        new_title = args.get("new_title")
        new_deadline_iso = args.get("new_deadline_iso")
        return await update_deadline_task_tool(task_id, new_title, new_deadline_iso)

    elif function_name == "log_climbing_activity":
        return await log_climbing_tool()

    elif function_name == "log_rest_day":
        return await log_rest_day_tool()

    elif function_name == "get_top_news":
        news = await get_top_news()
        return json.dumps(news, ensure_ascii=False)

    elif function_name == "get_weather_forecast":
        weather = await get_weather_forecast()
        return json.dumps(weather, ensure_ascii=False)

    return f"Herramienta '{function_name}' desconocida."


async def run_agent(user_message: str) -> str:
    try:
        system_prompt = get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        max_turns = 6
        for turn in range(max_turns):
            response = None
            last_exception = None

            # Fallback automático entre modelos si ocurre un Rate Limit 429
            for model_name in MODELS_TO_TRY:
                try:
                    kwargs = {
                        "model": model_name,
                        "messages": messages,
                        "max_tokens": 1500
                    }
                    if TOOLS_SCHEMA:
                        kwargs["tools"] = TOOLS_SCHEMA
                        kwargs["tool_choice"] = "auto"

                    response = await client.chat.completions.create(**kwargs)
                    break
                except Exception as err:
                    err_str = str(err)
                    if "429" in err_str or "rate_limit" in err_str.lower() or "ratelimit" in err_str.lower():
                        logger.warning(f"Rate limit 429 alcanzado en modelo '{model_name}'. Reintentando con modelo de respaldo...")
                        last_exception = err
                        continue
                    else:
                        raise err

            if response is None:
                if last_exception:
                    raise last_exception
                return "⚠️ No se pudo obtener respuesta de la IA en este momento."

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            raw_content = response_message.content or ""
            xml_calls = parse_xml_tool_calls(raw_content)

            if not tool_calls and not xml_calls:
                return clean_think_tags(raw_content)

            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments or "{}")
                    tool_result = await execute_tool_call(function_name, args)

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result
                    })

            elif xml_calls:
                messages.append({"role": "assistant", "content": raw_content})
                for call in xml_calls:
                    function_name = call["name"]
                    args = call["args"]
                    tool_result = await execute_tool_call(function_name, args)
                    messages.append({
                        "role": "user",
                        "content": f"Resultado de la herramienta {function_name}: {tool_result}"
                    })

        last_msg = messages[-1].get("content", "")
        return clean_think_tags(last_msg)

    except Exception as e:
        logger.error(f"Error en run_agent: {e}")
        return f"⚠️ Lo siento, ha ocurrido un error al procesar tu solicitud: {str(e)}"
