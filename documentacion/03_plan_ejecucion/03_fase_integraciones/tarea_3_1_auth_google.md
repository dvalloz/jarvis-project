# 🔹 Tarea 3.1 — Autenticación y Cliente de Google Calendar (`tools/calendar_tools.py`)

## 🎯 Objetivo
Construir el mecanismo de autenticación OAuth2 de Google que gestione el ciclo de vida de los tokens de acceso y refresco.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Implementar Flujo de Autenticación en `tools/calendar_tools.py`:**
   ```python
   import os
   from google.auth.transport.requests import Request
   from google.oauth2.credentials import Credentials
   from google_auth_oauthlib.flow import InstalledAppFlow
   from googleapiclient.discovery import build

   SCOPES = ['https://www.googleapis.com/auth/calendar']
   CREDENTIALS_PATH = 'credentials/google_credentials.json'
   TOKEN_PATH = 'credentials/google_token.json'

   def get_calendar_service():
       creds = None
       if os.path.exists(TOKEN_PATH):
           creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
       
       if not creds or not creds.valid:
           if creds and creds.expired and creds.refresh_token:
               creds.refresh(Request())
           else:
               flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
               creds = flow.run_local_server(port=0)
           
           with open(TOKEN_PATH, 'w') as token_file:
               token_file.write(creds.to_json())

       return build('calendar', 'v3', credentials=creds)
   ```

---

## ✅ Verificación de la Tarea
- Ejecutar la función por primera vez para completar la autorización en el navegador.
- Comprobar que se genere `credentials/google_token.json`.
