import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from openai import AsyncOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración del cliente LLM (Groq / OpenAI)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Carga de reglas configurables desde email_rules.json
# ---------------------------------------------------------------------------
_RULES_PATH = Path(__file__).parent.parent / "config" / "email_rules.json"

def _load_email_rules() -> Dict[str, Any]:
    """
    Carga las reglas de clasificación desde config/email_rules.json.
    Si el fichero no existe o no es válido, retorna reglas vacías sin crashear.
    """
    try:
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"email_rules.json no encontrado en {_RULES_PATH}. Usando reglas vacías.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando email_rules.json: {e}. Usando reglas vacías.")
        return {}

EMAIL_RULES: Dict[str, Any] = _load_email_rules()

# ---------------------------------------------------------------------------
# Capa 3 — Señales heurísticas bilingües (ES + EN)
# ---------------------------------------------------------------------------
SIGNALS_HIGH: List[str] = [
    # Financiero ES/EN
    r"\b(factura|invoice|pago|payment|cobro|cargo|adeudo|deuda|recibo|receipt)\b",
    r"\b(urgente|urgent|inmediato|immediate|cr[ií]tico|critical|importante|important)\b",
    r"\b(hacienda|agencia tributaria|declaraci[oó]n|irpf|iva|impuesto|tax|aeat)\b",
    r"\b(banco|bank|tarjeta|card|cuenta|account|transferencia|transfer|bizum)\b",
    r"\b(seguridad social|prestaci[oó]n|seguro|insurance|p[oó]liza|policy)\b",
    # Importes monetarios: €1.200, $500, 3.500€, 1,500 USD
    r"[\$€£]\s*\d[\d\.,]+|\d[\d\.,]+\s*[\$€£]|\d+[\.,]\d+\s*(euros?|usd|eur)",
    # Fechas límite
    r"\b(vence|vencimiento|deadline|plazo|expires?|expira|caduca|antes del)\b",
    # Legal / contractual
    r"\b(contrato|contract|acuerdo|agreement|firma|sign|notario|escritura|demanda|lawsuit)\b",
    # Salud
    r"\b(cita|appointment|m[eé]dico|doctor|hospital|anal[ií]tica|diagn[oó]stico|urgencias)\b",
    # Acceso / seguridad
    r"\b(inicio de sesi[oó]n sospechoso|acceso no autorizado|suspicious login|unauthorized access|cuenta bloqueada|account locked)\b",
]

SIGNALS_MEDIUM: List[str] = [
    r"\b(verificaci[oó]n|verification|confirma|confirm|acceso|access|activar|activate)\b",
    r"\b(actualizaci[oó]n|update|renovaci[oó]n|renewal|cambio|change)\b",
    r"\b(pedido|order|env[ií]o|shipment|entrega|delivery|seguimiento|tracking)\b",
    r"\b(recordatorio|reminder|aviso|notice|notificaci[oó]n|notification)\b",
]

# OTP / 2FA — siempre baja prioridad, nunca urgente
# Detecta tanto "código XXXXX" como "XXXXX código" en un rango de 60 chars
OTP_PATTERN: str = r"(c[oó]digo|code|otp|pin|clave|verification|verifica).{0,60}\b\d{4,8}\b|\b\d{4,8}\b.{0,60}(c[oó]digo|code|otp|pin|clave|verification|verifica)"


# ---------------------------------------------------------------------------
# CAPA 2 — Reglas duras (VIP / Bloqueados)
# ---------------------------------------------------------------------------

def _match_any_pattern(text: str, patterns: List[str]) -> bool:
    """Devuelve True si el texto coincide con alguno de los patrones regex."""
    for pattern in patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        except re.error as e:
            logger.warning(f"Patrón regex inválido '{pattern}': {e}")
    return False


def apply_hard_rules(sender: str, subject: str) -> Optional[Dict[str, Any]]:
    """
    Capa 2: aplica reglas duras desde email_rules.json.
    Retorna un resultado definitivo si hay match, o None para pasar a capas siguientes.

    Args:
        sender: Remitente del correo.
        subject: Asunto del correo.

    Returns:
        Dict con clasificación definitiva o None si no hay regla aplicable.
    """
    sender_lower = sender.lower().strip()

    # 1. Comprobar remitentes VIP exactos
    vip_senders: List[str] = EMAIL_RULES.get("vip_senders", [])
    for vip in vip_senders:
        if vip.lower() in sender_lower:
            logger.info(f"[Capa 2] VIP sender match: '{vip}' en '{sender}'")
            return {
                "is_important": True,
                "priority": "ALTA",
                "reason": f"Remitente VIP configurado: {vip}",
                "layer": 2
            }

    # 2. Comprobar patrones de remitente VIP (regex)
    vip_sender_patterns: List[str] = EMAIL_RULES.get("vip_sender_patterns", [])
    if _match_any_pattern(sender, vip_sender_patterns):
        logger.info(f"[Capa 2] VIP sender pattern match para: '{sender}'")
        return {
            "is_important": True,
            "priority": "ALTA",
            "reason": "Remitente de servicio de reservas/viajes",
            "layer": 2
        }

    # 3. Comprobar patrones de asunto VIP (reservas, vuelos, hoteles…)
    vip_subject_patterns: List[str] = EMAIL_RULES.get("vip_subject_patterns", [])
    if _match_any_pattern(subject, vip_subject_patterns):
        logger.info(f"[Capa 2] VIP subject pattern match para asunto: '{subject}'")
        return {
            "is_important": True,
            "priority": "ALTA",
            "reason": "Asunto relacionado con reserva o viaje",
            "layer": 2
        }

    # 4. Comprobar remitentes bloqueados exactos
    blocked_senders: List[str] = EMAIL_RULES.get("blocked_senders", [])
    for blocked in blocked_senders:
        if blocked.lower() in sender_lower:
            logger.info(f"[Capa 2] Blocked sender match: '{blocked}'")
            return {
                "is_important": False,
                "priority": "BAJA",
                "reason": f"Remitente bloqueado: {blocked}",
                "layer": 2
            }

    # 5. Comprobar patrones de remitente bloqueado
    blocked_sender_patterns: List[str] = EMAIL_RULES.get("blocked_sender_patterns", [])
    if _match_any_pattern(sender, blocked_sender_patterns):
        logger.info(f"[Capa 2] Blocked sender pattern match para: '{sender}'")
        return {
            "is_important": False,
            "priority": "BAJA",
            "reason": "Remitente de notificaciones de aplicación bloqueado",
            "layer": 2
        }

    # 6. Comprobar patrones de asunto bloqueado
    blocked_subject_patterns: List[str] = EMAIL_RULES.get("blocked_subject_patterns", [])
    if _match_any_pattern(subject, blocked_subject_patterns):
        logger.info(f"[Capa 2] Blocked subject pattern match para asunto: '{subject}'")
        return {
            "is_important": False,
            "priority": "BAJA",
            "reason": "Asunto bloqueado (notificación de app u oferta de empleo)",
            "layer": 2
        }

    return None  # Sin regla dura aplicable → pasa a Capa 3


# ---------------------------------------------------------------------------
# CAPA 3 — Heurística bilingüe mejorada
# ---------------------------------------------------------------------------

def evaluate_heuristic_multilingual(sender: str, subject: str) -> Optional[Dict[str, Any]]:
    """
    Capa 3: heurística bilingüe con niveles de confianza.
    - OTP detectado → no_importante (siempre transitorio).
    - ≥2 señales HIGH → importante con alta confianza (sin LLM).
    - Resto → None (pasa a Capa 4).

    Args:
        sender: Remitente del correo.
        subject: Asunto del correo.

    Returns:
        Dict con clasificación o None para pasar al LLM.
    """
    text = f"{sender} {subject}".lower()

    # Detectar OTP / 2FA → siempre baja prioridad
    if re.search(OTP_PATTERN, text, re.IGNORECASE):
        logger.info(f"[Capa 3] OTP/2FA detectado en: '{subject}'")
        return {
            "is_important": False,
            "priority": "BAJA",
            "reason": "Código OTP/2FA detectado — no requiere atención inmediata",
            "layer": 3
        }

    # Contar señales de alta confianza
    high_matches = []
    for pattern in SIGNALS_HIGH:
        try:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                high_matches.append(m.group(0))
        except re.error:
            pass

    if len(high_matches) >= 2:
        logger.info(f"[Capa 3] Alta confianza ({len(high_matches)} señales): {high_matches[:3]} en '{subject}'")
        return {
            "is_important": True,
            "priority": "ALTA",
            "reason": f"Heurística multicapa: {len(high_matches)} indicadores críticos detectados ({', '.join(high_matches[:2])})",
            "layer": 3
        }

    # Con 0 o 1 señales → pasa a Capa 4 (LLM)
    return None


# ---------------------------------------------------------------------------
# CAPA 3 fallback — heurística de respaldo (para cuando LLM falla)
# ---------------------------------------------------------------------------
CRITICAL_KEYWORDS = [
    "urgente", "seguridad", "transferencia", "banco", "hacienda", "tributaria",
    "bloqueo", "fraude", "contrato", "factura", "nómina", "nomina", "cita",
    "médica", "medica", "importante", "alerta", "autorizar", "firma",
    "urgent", "payment", "invoice", "account", "blocked", "security"
]

def evaluate_email_importance_heuristic(sender: str, subject: str) -> Dict[str, Any]:
    """
    Evaluación heurística determinista local de respaldo.
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


# ---------------------------------------------------------------------------
# CAPA 4 — LLM con contexto enriquecido y few-shot de correcciones
# ---------------------------------------------------------------------------

def _build_enriched_system_prompt(recent_corrections: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Construye el system prompt enriquecido con contexto de David y few-shot de correcciones.

    Args:
        recent_corrections: Lista de dicts con 'sender', 'subject', 'was_important' (bool).

    Returns:
        String con el prompt de sistema.
    """
    base = """Eres el clasificador de correos electrónicos personal de David, un profesional en España.

CONTEXTO DE DAVID:
- Sus servicios bancarios, hacienda, seguros, médico y trabajo son siempre importantes.
- Correos de GitHub, LinkedIn, Slack, Trello, Notion y redes sociales son ruido — no importantes.
- Ofertas de empleo de empresas externas no son importantes.
- Reservas de vuelos, hoteles, trenes y restaurantes son siempre importantes.
- Cursos de The Big School y Commit Academy son importantes para su formación.

POLÍTICA ZERO-PII: Por privacidad estricta, NUNCA recibirás el cuerpo del correo.
Clasifica ÚNICAMENTE con remitente y asunto.

REGLAS DE EVALUACIÓN:
1. IMPORTANTE (is_important: true):
   - Alertas bancarias, cargos, transferencias, bloqueos de cuenta.
   - Notificaciones oficiales: Hacienda, Seguridad Social, DGT, sanidad pública.
   - Asuntos laborales directos: nóminas, contratos, reuniones urgentes.
   - Seguridad: accesos sospechosos, recuperación de cuenta.
   - Reservas y confirmaciones de viajes, hoteles, restaurantes.
   - Facturas e importes a pagar o cobrar.

2. NO IMPORTANTE (is_important: false):
   - Promociones, newsletters, publicidad.
   - Resúmenes automáticos de redes sociales o foros.
   - Notificaciones de apps (GitHub, Jira, Slack, LinkedIn…).
   - Ofertas de empleo de empresas externas.
   - Códigos OTP / 2FA (ya filtrados, pero si llegan → false)."""

    if recent_corrections:
        corrections_text = "\n\nEJEMPLOS DE CORRECCIONES RECIENTES DEL USUARIO (few-shot):\n"
        for c in recent_corrections[:10]:
            verdict = "IMPORTANTE" if c.get("was_important") else "NO IMPORTANTE"
            corrections_text += (
                f"- Remitente: {c.get('sender', '')} | Asunto: {c.get('subject', '')} → {verdict}\n"
            )
        base += corrections_text

    base += """

Responde SIEMPRE y ÚNICAMENTE con un objeto JSON válido:
{
    "is_important": true o false,
    "priority": "ALTA" | "MEDIA" | "BAJA",
    "reason": "Explicación concisa en una frase"
}"""

    return base


async def evaluate_email_importance_llm(
    sender: str,
    subject: str,
    recent_corrections: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Capa 4: evalúa la importancia del correo mediante LLM con prompt enriquecido.
    Zero-PII garantizado: solo sender y subject llegan al modelo.

    Args:
        sender: Nombre y dirección del remitente.
        subject: Asunto del correo.
        recent_corrections: Últimas correcciones del usuario para few-shot.

    Returns:
        Dict con 'is_important' (bool), 'priority' (str) y 'reason' (str).
    """
    clean_sender = sender.strip() if sender else "Desconocido"
    clean_subject = subject.strip() if subject else "(Sin Asunto)"

    system_prompt = _build_enriched_system_prompt(recent_corrections)

    user_prompt = f"""<email>
  <sender>{clean_sender}</sender>
  <subject>{clean_subject}</subject>
</email>"""

    for model_name in MODELS_TO_TRY:
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
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
            logger.info(f"[Capa 4] LLM ({model_name}) clasificó '{clean_subject}' → {parsed.get('is_important')}")
            return {
                "is_important": bool(parsed.get("is_important", False)),
                "priority": str(parsed.get("priority", "BAJA")).upper(),
                "reason": str(parsed.get("reason", "Clasificado por IA")),
                "layer": 4
            }
        except Exception as e:
            logger.warning(f"Error clasificando email con modelo {model_name}: {e}. Intentando fallback...")
            continue

    # Si todos los modelos de IA fallan, recurre a la heurística local
    logger.info("Todos los modelos LLM no disponibles o con error de parseo. Aplicando heurística local.")
    result = evaluate_email_importance_heuristic(clean_sender, clean_subject)
    result["layer"] = 3
    return result


# ---------------------------------------------------------------------------
# PIPELINE UNIFICADO — triage_email (punto de entrada público)
# ---------------------------------------------------------------------------

async def triage_email(
    email_metadata: Dict[str, Any],
    recent_corrections: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Pipeline unificado de clasificación Zero-PII con 4 capas en cascada:

    Capa 1 (existente): Cabeceras técnicas / labels Gmail → descarta promos.
    Capa 2 (NUEVA): Reglas duras VIP/bloqueados desde email_rules.json.
    Capa 3 (NUEVA): Heurística bilingüe ES+EN con regex (importes, fechas, OTP).
    Capa 4 (MEJORADA): LLM con prompt enriquecido + few-shot de correcciones.

    Args:
        email_metadata: Diccionario obtenido de parse_email_metadata().
        recent_corrections: Últimas correcciones del usuario (opcional) para Capa 4.

    Returns:
        Dict con 'is_important', 'is_promotional', 'priority', 'reason', 'layer'.
    """
    sender = email_metadata.get("sender", "")
    subject = email_metadata.get("subject", "")
    is_promo_flag = email_metadata.get("is_promotional", False)

    # ------------------------------------------------------------------
    # CAPA 1: Filtro determinista de cabeceras (comportamiento original)
    # Si el email viene de CATEGORY_PROMOTIONS, lo evaluamos igualmente
    # con las reglas duras (Capa 2) para rescatar emails VIP que Gmail
    # haya clasificado erróneamente como promociones.
    # ------------------------------------------------------------------
    if is_promo_flag:
        # Pasar por Capa 2 antes de descartar (puede ser un VIP)
        hard_rule = apply_hard_rules(sender, subject)
        if hard_rule and hard_rule["is_important"]:
            logger.info(f"[Capa 1→2] Email promo rescatado por regla VIP: '{subject}'")
            return {
                "is_important": True,
                "is_promotional": True,
                "priority": hard_rule["priority"],
                "reason": hard_rule["reason"],
                "layer": hard_rule.get("layer", 2)
            }
        # Sin regla VIP → descarta como promo (comportamiento original)
        return {
            "is_important": False,
            "is_promotional": True,
            "priority": "BAJA",
            "reason": "Descartado localmente por cabeceras de publicidad/newsletter"
        }

    # ------------------------------------------------------------------
    # CAPA 2: Reglas duras (VIP / Bloqueados)
    # ------------------------------------------------------------------
    hard_rule = apply_hard_rules(sender, subject)
    if hard_rule is not None:
        return {
            "is_important": hard_rule["is_important"],
            "is_promotional": False,
            "priority": hard_rule["priority"],
            "reason": hard_rule["reason"],
            "layer": hard_rule.get("layer", 2)
        }

    # ------------------------------------------------------------------
    # CAPA 3: Heurística bilingüe mejorada
    # ------------------------------------------------------------------
    heuristic_result = evaluate_heuristic_multilingual(sender, subject)
    if heuristic_result is not None:
        return {
            "is_important": heuristic_result["is_important"],
            "is_promotional": False,
            "priority": heuristic_result["priority"],
            "reason": heuristic_result["reason"],
            "layer": heuristic_result.get("layer", 3)
        }

    # ------------------------------------------------------------------
    # CAPA 4: LLM enriquecido (solo para emails genuinamente ambiguos)
    # ------------------------------------------------------------------
    eval_result = await evaluate_email_importance_llm(sender, subject, recent_corrections)
    return {
        "is_important": eval_result.get("is_important", False),
        "is_promotional": False,
        "priority": eval_result.get("priority", "BAJA"),
        "reason": eval_result.get("reason", ""),
        "layer": eval_result.get("layer", 4)
    }
