"""
Script para realizar la autenticación inicial interactiva de Google Calendar OAuth2.
Ejecuta este script desde tu terminal:
    .venv\Scripts\python auth_google.py
Se abrirá una ventana de tu navegador para autorizar a Jarvis a acceder a tu Google Calendar.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.calendar_tools import get_calendar_service

def main():
    print("=" * 60)
    print("   AUTENTICACIÓN INICIAL OAUTH2 - GOOGLE CALENDAR")
    print("=" * 60)
    print("\nIniciando servidor local de autorización...")
    print("Se abrirá tu navegador web predeterminado. Inicia sesión con la cuenta")
    print("de Google donde gestionas tu calendario y concede los permisos solicitados.\n")

    try:
        service = get_calendar_service(interactive=True)
        print("\n✅ ¡Autenticación completada con éxito!")
        print("Se ha generado y guardado el token en 'credentials/google_token.json'.")
    except Exception as e:
        print(f"\n❌ Error durante la autenticación: {e}")

if __name__ == "__main__":
    main()
