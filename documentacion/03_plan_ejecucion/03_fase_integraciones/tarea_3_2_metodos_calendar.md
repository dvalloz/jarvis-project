# 🔹 Tarea 3.2 — Métodos Operativos de Calendar (`get_day_events`, `create_calendar_event`)

## 🎯 Objetivo
Desarrollar funciones auxiliares para recuperar la agenda del día e insertar nuevos eventos respetando la zona horaria del usuario.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Añadir Funciones a `tools/calendar_tools.py`:**
   ```python
   from datetime import datetime, date
   import pytz
   from config.settings import settings

   def get_day_events(target_date: date):
       service = get_calendar_service()
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

   def create_calendar_event(summary: str, start_iso: str, end_iso: str, description: str = ""):
       service = get_calendar_service()
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
   ```

---

## ✅ Verificación de la Tarea
- Consultar los eventos de hoy desde una consola Python y verificar que retorne la lista de citas sin errores de API.
