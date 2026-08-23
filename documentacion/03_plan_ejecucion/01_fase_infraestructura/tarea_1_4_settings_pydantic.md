# 🔹 Tarea 1.4 — Gestión de Dependencias y Configuración Centralizada

## 🎯 Objetivo
Definir las dependencias del proyecto en `requirements.txt` y construir un módulo centralizado `config/settings.py` basado en `pydantic-settings` para validar las variables de entorno al iniciar la app.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Definir `requirements.txt`:**
   Crea el archivo `requirements.txt` en la raíz con las librerías necesarias:
   ```text
   python-telegram-bot>=21.0
   sqlalchemy[asyncio]>=2.0.0
   asyncpg>=0.29.0
   pydantic-settings>=2.0.0
   google-api-python-client>=2.100.0
   google-auth-oauthlib>=1.1.0
   google-auth-httplib2>=0.1.1
   apscheduler>=3.10.0
   openai>=1.0.0
   pytz>=2023.3
   ```

2. **Crear archivo `.env.example`:**
   ```env
   TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyZ"
   TELEGRAM_USER_ID=123456789
   DATABASE_URL="postgresql+asyncpg://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
   OPENAI_API_KEY="sk-proj-..."
   TIMEZONE="Europe/Madrid"
   ```

3. **Implementar `config/settings.py`:**
   ```python
   from pydantic_settings import BaseSettings, SettingsConfigDict
   from pydantic import Field

   class Settings(BaseSettings):
       telegram_bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
       telegram_user_id: int = Field(..., validation_alias="TELEGRAM_USER_ID")
       database_url: str = Field(..., validation_alias="DATABASE_URL")
       openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
       timezone: str = Field("Europe/Madrid", validation_alias="TIMEZONE")

       model_config = SettingsConfigDict(
           env_file=".env",
           env_file_encoding="utf-8",
           extra="ignore"
       )

   settings = Settings()
   ```

---

## ✅ Verificación de la Tarea
- Ejecutar un test rápido en consola Python:
  ```python
  from config.settings import settings
  print(settings.telegram_user_id)
  ```
- Confirmar que cargue correctamente los valores desde `.env`.
