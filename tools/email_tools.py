import os
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly'
]
CREDENTIALS_PATH = 'credentials/google_credentials.json'
TOKEN_PATH = 'credentials/google_token.json'


def get_gmail_service(interactive: bool = False):
    """
    Obtiene el cliente autenticado de la API de Gmail (v1) con alcance de solo lectura.
    Reutiliza el flujo de credenciales OAuth de Google compartido con Google Calendar.

    Args:
        interactive: Si es True, permite levantar servidor local para login manual.

    Returns:
        Google API Resource para interactuar con la API de Gmail.

    Raises:
        FileNotFoundError: Si no se localiza google_credentials.json.
        RuntimeError: Si las credenciales no son válidas y no se está en modo interactivo.
    """
    creds = None
    if os.path.exists(TOKEN_PATH) and os.path.getsize(TOKEN_PATH) > 10:
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, GMAIL_SCOPES)
        except Exception as e:
            logger.warning(f"No se pudo cargar token desde {TOKEN_PATH}: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Error al refrescar token de Google: {e}")
                creds = None

        if not creds or not creds.valid:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"No se encontró el archivo de credenciales en '{CREDENTIALS_PATH}'.")

            if not interactive:
                raise RuntimeError(
                    "El token de Google no cuenta con autorización o ha expirado. "
                    "Ejecuta la autenticación inicial interactiva para regenerar google_token.json."
                )

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)

        if creds and creds.valid:
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
                token_file.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def parse_email_metadata(message_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parsea de forma segura los metadatos de un mensaje de Gmail sin inspeccionar el cuerpo.
    Aplica la política estricta Zero-PII: solo procesa remitente, asunto, fecha y cabeceras técnicas.

    Args:
        message_raw: Diccionario devuelto por la API de Gmail con formato 'metadata'.

    Returns:
        Dict con los campos normalizados:
            - message_id (str): Identificador único de Gmail.
            - thread_id (str): ID del hilo de conversación.
            - sender (str): Remitente ('From').
            - subject (str): Asunto ('Subject').
            - received_at (datetime): Fecha de recepción en UTC.
            - labels (List[str]): Etiquetas de Gmail (ej. UNREAD, INBOX, CATEGORY_PROMOTIONS).
            - is_promotional (bool): True si contiene cabeceras o etiquetas típicas de publicidad/boletín.
    """
    msg_id = message_raw.get("id", "")
    thread_id = message_raw.get("threadId", "")
    labels = message_raw.get("labelIds", [])

    payload = message_raw.get("payload", {})
    headers_list = payload.get("headers", [])

    # Indexar cabeceras en minúsculas para acceso rápido insensible a mayúsculas
    headers_map = {}
    for h in headers_list:
        name = h.get("name", "").lower()
        val = h.get("value", "")
        headers_map[name] = val

    sender = headers_map.get("from", "Remitente Desconocido")
    subject = headers_map.get("subject", "(Sin Asunto)")

    # Parsear fecha
    date_str = headers_map.get("date")
    received_at = None
    if date_str:
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = None

    if not received_at:
        # Fallback a internalDate (timestamp en milisegundos provisto por Gmail)
        internal_date_ms = message_raw.get("internalDate")
        if internal_date_ms:
            try:
                received_at = datetime.fromtimestamp(int(internal_date_ms) / 1000.0, tz=timezone.utc)
            except Exception:
                received_at = datetime.now(timezone.utc)
        else:
            received_at = datetime.now(timezone.utc)

    # Detección determinista de publicidad / newsletter
    has_unsubscribe = bool(headers_map.get("list-unsubscribe"))
    is_bulk = headers_map.get("precedence", "").lower() in ("bulk", "list")
    is_promo_label = any(lbl in ("CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "SPAM") for lbl in labels)

    is_promotional = has_unsubscribe or is_bulk or is_promo_label

    return {
        "message_id": msg_id,
        "thread_id": thread_id,
        "sender": sender,
        "subject": subject,
        "received_at": received_at,
        "labels": labels,
        "is_promotional": is_promotional
    }


def fetch_unread_emails_metadata(service, max_results: int = 15, query: str = "is:unread") -> List[Dict[str, Any]]:
    """
    Obtiene los correos no leídos solicitando estrictamente 'format=metadata'.
    De esta forma, la API de Gmail no descarga el cuerpo ni contenido textual del mensaje,
    garantizando que ningún dato sensible salga del perímetro por red.

    Args:
        service: Cliente de Gmail API.
        max_results: Cantidad máxima de mensajes a listar por llamada.
        query: Parámetro de búsqueda de Gmail (por defecto 'is:unread').

    Returns:
        Lista de diccionarios con metadatos procesados por parse_email_metadata().
    """
    try:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        messages = response.get("messages", [])
        if not messages:
            return []

        results = []
        for msg_summary in messages:
            msg_id = msg_summary.get("id")
            if not msg_id:
                continue

            # Petición con format='metadata' para no descargar el cuerpo del mensaje
            raw_msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe", "Precedence"]
            ).execute()

            parsed = parse_email_metadata(raw_msg)
            results.append(parsed)

        return results

    except Exception as e:
        logger.error(f"Error al consultar correos no leídos en Gmail API: {e}")
        return []
