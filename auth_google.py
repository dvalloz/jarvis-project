"""
Script para realizar la autenticación inicial interactiva de Google OAuth2 (Google Calendar + Gmail API).
Ejecuta este script desde tu terminal local (donde dispongas de navegador web):
    .venv\Scripts\python auth_google.py
Se abrirá una ventana de tu navegador para autorizar a Jarvis a acceder a tu Google Calendar y leer tus correos de Gmail.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.email_tools import get_gmail_service

def main():
    print("=" * 60)
    print("   AUTENTICACIÓN INICIAL OAUTH2 - GOOGLE (CALENDAR + GMAIL)")
    print("=" * 60)
    print("\nIniciando servidor local de autorización...")
    print("Se abrirá tu navegador web predeterminado. Inicia sesión con tu cuenta")
    print("de Google y concede los permisos solicitados para Calendario y Gmail.\n")

    try:
        # get_gmail_service solicita scopes de Calendar y Gmail readonly
        service = get_gmail_service(interactive=True)
        print("\n✅ ¡Autenticación completada con éxito!")
        print("Se ha generado y guardado el token con permisos de Calendar y Gmail en 'credentials/google_token.json'.")
    except Exception as e:
        print(f"\n❌ Error durante la autenticación: {e}")

if __name__ == "__main__":
    main()
