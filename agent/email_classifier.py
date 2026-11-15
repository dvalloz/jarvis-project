import json
import logging
import re
from typing import Dict, Any, Optional

from openai import AsyncOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

# Configuración del cliente LLM (Groq / OpenAI) compatible con agent/engine.py
is_groq = settings.groq_api_key and settings.groq_api_key.startswith("gsk_")
if is_groq:
    client = AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    MODELS_TO_TRY = [
        "qwen/qwen3.6-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b"
    ]
else:
    client = AsyncOpenAI(
        api_key=settings.openai_api_key
    )
    MODELS_TO_TRY = ["gpt-4o-mini"]

SYSTEM_PROMPT = """Eres el clasificador de correos electrónicos de Jarvis, un asistente personal inteligente.
Tu misión es evaluar la urgencia e importancia de un correo electrónico basándote ÚNICA Y EXCLUSIVAMENTE en los metadatos proporcionados: REMITENTE y ASUNTO.
Por políticas de privacidad estrictas (Zero-PII), jamás tendrás acceso al cuerpo del correo.

Reglas de Evaluación:
1. IMPORTANTE (is_important: true):
   - Alertas bancarias, autorizaciones de transferencias, cargos no reconocidos o bloqueos de tarjetas.
   - Notificaciones oficiales: Agencia Tributaria (Hacienda), Seguridad Social, DGT, citas médicas.
   - Asuntos laborales directos: nóminas, contratos, convocatorias de reuniones urgentes, clientes clave.
   - Seguridad: alertas de inicio de sesión sospechoso o recuperación de cuentas sensibles.

2. NO IMPORTANTE / SECUNDARIO (is_important: false):
   - Promociones, ofertas, descuentos, boletines informativos (newsletters), publicidad.
   - Resúmenes automáticos de redes sociales o foros.
   - Confirmaciones rutinarias de envíos de paquetería ya entregados o comunicaciones generales no urgentes.

Debes responder SIEMPRE y ÚNICAMENTE con un objeto JSON válido con este formato:
{
    "is_important": true o false,
    "priority": "ALTA" | "MEDIA" | "BAJA",
    "reason": "Explicación concisa en una frase del motivo"
}"""

CRITICAL_KEYWORDS = [
    "urgente", "seguridad", "transferencia", "banco", "hacienda", "tributaria",
    "bloqueo", "fraude", "contrato", "factura", "nómina", "nomina", "cita",
    "médica", "medica", "importante", "alerta", "autorizar", "firma"
]


def evaluate_email_importance_heuristic(sender: str, subject: str) -> Dict[str, Any]:
    """
    Evaluación heurística determinista local basada en palabras clave críticas.
    Se utiliza como mecanismo de alta disponibilidad ante caídas de red o cuota de LLM.

    Args:
        sender: Remitente del mensaje.
        subject: Asunto del mensaje.

    Returns:
        Dict con 'is_important', 'priority' y 'reason'.
    """
    text_to_check = f"{sender} {subject}".lower()
    for kw in CRITICAL_KEYWORDS:
        if kw in text_to_check:
            return {
                "is_important": True,
                "priority": "ALTA",
                "reason": f"Detectado indicador crítico en asunto/remitente ('{kw}')"
            }

    return {
        "is_important": False,
        "priority": "BAJA",
        "reason": "Metadatos sin indicadores de urgencia detectados"
    }


async def evaluate_email_importance_llm(sender: str, subject: str) -> Dict[str, Any]:
    """
    Evalúa la importancia de un correo mediante inferencia con LLM utilizando exclusivamente
    metadatos sanitizados (Remitente + Asunto). Cero exposición de datos privados corporales.

    Args:
        sender: Nombre y dirección del remitente.
        subject: Asunto del correo.

    Returns:
        Dict con 'is_important' (bool), 'priority' (str) y 'reason' (str).
    """
    clean_sender = sender.strip() if sender else "Desconocido"
    clean_subject = subject.strip() if subject else "(Sin Asunto)"

    user_prompt = f"Remitente: {clean_sender}\nAsunto: {clean_subject}"

    for model_name in MODELS_TO_TRY:
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )

            raw_text = response.choices[0].message.content or ""
            # Limpiar posibles bloques markdown de código ```json ... ```
            cleaned = re.sub(r'```json\s*', '', raw_text)
            cleaned = re.sub(r'```', '', cleaned).strip()

            parsed = json.loads(cleaned)
            return {
                "is_important": bool(parsed.get("is_important", False)),
                "priority": str(parsed.get("priority", "BAJA")).upper(),
                "reason": str(parsed.get("reason", "Clasificado por IA"))
            }
        except Exception as e:
            logger.warning(f"Error clasificando email con modelo {model_name}: {e}. Intentando fallback...")
            continue

    # Si todos los modelos de IA fallan, recurre a la heurística local
    logger.info("Todos los modelos LLM no disponibles o con error de parseo. Aplicando heurística local.")
    return evaluate_email_importance_heuristic(clean_sender, clean_subject)


async def triage_email(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline unificado de clasificación Zero-PII:
    1. Si las cabeceras técnicas indican publicidad o newsletter -> Se descarta localmente (Cero LLM).
    2. Si es potencialmente relevante -> Se evalúa con IA usando únicamente remitente y asunto.

    Args:
        email_metadata: Diccionario obtenido de parse_email_metadata().

    Returns:
        Dict con 'is_important', 'is_promotional', 'priority', 'reason'.
    """
    is_promo = email_metadata.get("is_promotional", False)
    if is_promo:
        return {
            "is_important": False,
            "is_promotional": True,
            "priority": "BAJA",
            "reason": "Descartado localmente por cabeceras de publicidad/newsletter"
        }

    sender = email_metadata.get("sender", "")
    subject = email_metadata.get("subject", "")

    eval_result = await evaluate_email_importance_llm(sender, subject)
    return {
        "is_important": eval_result.get("is_important", False),
        "is_promotional": False,
        "priority": eval_result.get("priority", "BAJA"),
        "reason": eval_result.get("reason", "")
    }
