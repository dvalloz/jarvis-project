# 📍 Fase 1: Configuración de Infraestructura, Accesos y Entorno (Resumen de Fase)

Esta fase establece las bases del proyecto preparando el bot de Telegram, los accesos OAuth2 a la API de Google Calendar, el entorno de base de datos PostgreSQL mediante Docker Compose y el sistema de gestión de dependencias y variables de entorno en Python.

---

## 📂 Documentos de Tarea Incluidos

1. 🔹 [Tarea 1.1 — Creación y Securización del Bot de Telegram](./tarea_1_1_bot_telegram.md)
2. 🔹 [Tarea 1.2 — Configuración de Google Cloud y OAuth2](./tarea_1_2_google_oauth.md)
3. 🔹 [Tarea 1.3 — Infraestructura de Persistencia con Docker Compose](./tarea_1_3_docker_compose.md)
4. 🔹 [Tarea 1.4 — Gestión de Dependencias y Configuración Centralizada](./tarea_1_4_settings_pydantic.md)

---

## 🎯 Entregables Globales de la Fase

* Bot de Telegram activo con token securizado y restringido por User ID.
* Credenciales `credentials/google_credentials.json` listas para el flujo OAuth.
* Contenedor de PostgreSQL 16 declarado y probado mediante `docker-compose.yml`.
* Módulo `config/settings.py` con validación estricta Pydantic para el archivo `.env`.
