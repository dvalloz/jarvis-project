# 🔹 Tarea 1.3 — Infraestructura de Persistencia con Docker Compose

## 🎯 Objetivo
Configurar el entorno de base de datos relacional con PostgreSQL 16 utilizando Docker Compose, garantizando el aislamiento de datos y la persistencia local.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `docker-compose.yml`:**
   En la raíz del proyecto, crea el archivo `docker-compose.yml` con la declaración del servicio PostgreSQL:

   ```yaml
   version: '3.8'

   services:
     db:
       image: postgres:16-alpine
       container_name: jarvis_postgres_db
       restart: always
       environment:
         POSTGRES_USER: ${POSTGRES_USER:-jarvis_user}
         POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-jarvis_password}
         POSTGRES_DB: ${POSTGRES_DB:-jarvis_db}
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-jarvis_user} -d ${POSTGRES_DB:-jarvis_db}"]
         interval: 5s
         timeout: 5s
         retries: 5

   volumes:
     postgres_data:
       driver: local
   ```

2. **Actualizar el archivo `.env`:**
   Añade la URL de conexión a la base de datos en tu `.env`:
   ```env
   POSTGRES_USER=jarvis_user
   POSTGRES_PASSWORD=jarvis_password
   POSTGRES_DB=jarvis_db
   DATABASE_URL=postgresql+asyncpg://jarvis_user:jarvis_password@localhost:5432/jarvis_db
   ```

---

## ✅ Verificación de la Tarea
- Arrancar el servicio de base de datos:
  ```bash
  docker compose up -d db
  ```
- Comprobar que el contenedor esté `healthy`:
  ```bash
  docker ps
  ```
