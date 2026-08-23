# 🔹 Tarea 6.2 — Orquestación Completa en Compose (`docker-compose.yml`)

## 🎯 Objetivo
Orquestar los servicios `db` (PostgreSQL) y `bot` (Telegram AI Assistant) en un único archivo `docker-compose.yml` garantizando persistencia y reinicios automáticos.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Actualizar `docker-compose.yml` completo:**
   ```yaml
   version: '3.8'

   services:
     db:
       image: postgres:16-alpine
       container_name: jarvis_postgres_db
       restart: unless-stopped
       environment:
         POSTGRES_USER: ${POSTGRES_USER:-jarvis_user}
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-jarvis_password}
         POSTGRES_DB: ${POSTGRES_DB:-jarvis_db}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-jarvis_user} -d ${POSTGRES_DB:-jarvis_db}"]
         interval: 5s
         timeout: 5s
         retries: 5

     bot:
       build: .
       container_name: jarvis_bot_app
       restart: unless-stopped
       env_file:
         - .env
       volumes:
         - ./credentials:/app/credentials
         - ./logs:/app/logs
       depends_on:
         db:
           condition: service_healthy

   volumes:
     postgres_data:
       driver: local
   ```

---

## ✅ Verificación de la Tarea
- Ejecutar `docker compose up -d` y verificar con `docker compose logs -f bot` que el bot conecte con la base de datos de inmediato.
