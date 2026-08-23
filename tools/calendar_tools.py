import os
import logging
from datetime import datetime, date, timedelta
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config.settings import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_PATH = 'credentials/google_credentials.json'
TOKEN_PATH = 'credentials/google_token.json'

def get_calendar_service(interactive: bool = False):
    creds = None
    if os.path.exists(TOKEN_PATH) and os.path.getsize(TOKEN_PATH) > 10:
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
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
                    "El token de Google Calendar no está autenticado aún. "
                    "Ejecuta la autenticación inicial interactiva para generar google_token.json."
                )

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        if creds and creds.valid:
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
                token_file.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def get_day_events(target_date: date):
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    service = get_calendar_service(interactive=False)
    tz = pytz.timezone(settings.timezone)

    start_dt = tz.localize(datetime.combine(target_date, datetime.min.time())).isoformat()
    end_dt = tz.localize(datetime.combine(target_date, datetime.max.time())).isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_dt,
        timeMax=end_dt,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    formatted_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'Sin título')
        formatted_events.append({
            "summary": summary,
            "start": start,
            "description": event.get('description', '')
        })
    return formatted_events

def get_week_events(start_date: date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    # Si la fecha dada no es Lunes, calcular el Lunes de esa semana
    monday = start_date - timedelta(days=start_date.weekday())
    sunday = monday + timedelta(days=6)

    service = get_calendar_service(interactive=False)
    tz = pytz.timezone(settings.timezone)

    start_dt = tz.localize(datetime.combine(monday, datetime.min.time())).isoformat()
    end_dt = tz.localize(datetime.combine(sunday, datetime.max.time())).isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_dt,
        timeMax=end_dt,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    formatted_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'Sin título')
        formatted_events.append({
            "summary": summary,
            "start": start,
            "description": event.get('description', '')
        })
    return formatted_events

def create_calendar_event(summary: str, start_iso: str, end_iso: str, description: str = ""):
    service = get_calendar_service(interactive=False)
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_iso,
            'timeZone': settings.timezone,
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': settings.timezone,
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event_body).execute()
    return created_event.get('htmlLink')
