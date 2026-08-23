# 📋 Desglose de Fases, Tareas y Criterios de Aceptación

Este documento contiene la matriz completa de planificación del proyecto **Telegram Personal AI Assistant**, estructurado en 6 Fases y 20 Tareas técnicas.

---

## 📍 Fase 1: Configuración de Infraestructura, Accesos y Entorno

### 🔹 Tarea 1.1 — Creación y Securización del Bot de Telegram
* **Objetivo:** Generar el bot en Telegram y obtener las credenciales de identificación y securización.
* **Dependencias:** Ninguna.
* **Entregables:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_USER_ID` anotados en `.env`.
* **Criterios de Aceptación:** Bot creado mediante BotFather, opción de unir a grupos desactivada, ID de usuario personal obtenido y validado.

### 🔹 Tarea 1.2 — Configuración de Google Cloud y OAuth2
* **Objetivo:** Configurar el proyecto en Google Cloud y habilitar la Google Calendar API.
* **Dependencias:** Cuenta de Google.
* **Entregables:** Archivo `credentials/google_credentials.json`.
* **Criterios de Aceptación:** Proyecto en Google Cloud activo, API habilitada, pantalla OAuth en Testing con el correo del usuario, credenciales Desktop descargadas en la ruta esperada.

### 🔹 Tarea 1.3 — Infraestructura de Persistencia con Docker Compose
* **Objetivo:** Definir el contenedor de PostgreSQL para desarrollo y producción local.
* **Dependencias:** Docker y Docker Compose instalados.
* **Entregables:** Archivo `docker-compose.yml`.
* **Criterios de Aceptación:** Servicio `db` configurado con PostgreSQL 16, volúmenes locales persistentes (`postgres_data`), puertos mapeados y comprobación de salud (*healthcheck*).

### 🔹 Tarea 1.4 — Gestión de Dependencias y Configuración Centralizada
* **Objetivo:** Definir paquetes de Python y validación de variables de entorno con Pydantic.
* **Dependencias:** Tareas 1.1, 1.2, 1.3.
* **Entregables:** `requirements.txt`, `.env.example`, `config/settings.py`.
* **Criterios de Aceptación:** Entorno virtual funcional, `settings.py` valida todas las variables requeridas al arrancar y lanza error explícito si falta alguna clave.

---

## 📍 Fase 2: Modelado de Datos y Capa de Persistencia

### 🔹 Tarea 2.1 — Definición de Esquemas ORM (`database/models.py`)
* **Objetivo:** Diseñar el modelo relacional de la base de datos con SQLAlchemy Async.
* **Dependencias:** Tarea 1.4.
* **Entregables:** File `database/models.py`.
* **Criterios de Aceptación:** Tablas `workouts`, `workout_logs`, `recurring_tasks` y `quick_reminders` definidas con tipos de datos correctos, claves primarias y relaciones.

### 🔹 Tarea 2.2 — Conexión y Sesión Asíncrona (`database/connection.py`)
* **Objetivo:** Implementar la gestión asíncrona de conexiones a PostgreSQL mediante `asyncpg`.
* **Dependencias:** Tarea 2.1.
* **Entregables:** File `database/connection.py`.
* **Criterios de Aceptación:** `async_engine` y `async_sessionmaker` creados, generador de sesiones `get_db()` funcional con context manager asíncrono.

### 🔹 Tarea 2.3 — Implementación de Operaciones CRUD (`database/crud.py`)
* **Objetivo:** Desarrollar las funciones de base de datos deterministas para las rutinas, logs y tareas.
* **Dependencias:** Tarea 2.2.
* **Entregables:** File `database/crud.py`.
* **Criterios de Aceptación:** Funciones `get_next_workout_routine()`, `log_completed_workout()`, `get_due_recurring_tasks()` y `mark_task_completed()` probadas y operativas.

### 🔹 Tarea 2.4 — Script de Inicialización y Sembrado (`database/seed.py`)
* **Objetivo:** Poblar la base de datos con las rutinas de gimnasio iniciales y tareas del hogar.
* **Dependencias:** Tareas 2.1 - 2.3.
* **Entregables:** File `database/seed.py`.
* **Criterios de Aceptación:** Creación automática de tablas si no existen e inserción idempotente del catálogo inicial de rutinas y tareas.

---

## 📍 Fase 3: Integraciones Externas y Herramientas del Agente (Tools)

### 🔹 Tarea 3.1 — Autenticación y Cliente de Google Calendar (`tools/calendar_tools.py`)
* **Objetivo:** Implementar el flujo OAuth2 para interactuar con la Google Calendar API.
* **Dependencias:** Tarea 1.2.
* **Entregables:** Lógica OAuth2 en `tools/calendar_tools.py`.
* **Criterios de Aceptación:** Generación y actualización transparente del token de acceso (`google_token.json`).

### 🔹 Tarea 3.2 — Métodos Operativos de Calendar
* **Objetivo:** Crear funciones para consultar e insertar eventos en la agenda.
* **Dependencias:** Tarea 3.1.
* **Entregables:** Funciones `get_day_events()` y `create_calendar_event()`.
* **Criterios de Aceptación:** Lectura precisa de eventos entre 00:00 y 23:59 en zona horaria local e inserción de eventos validada en Google Calendar.

### 🔹 Tarea 3.3 — Envoltorios de Herramientas para el LLM (`tools/registry.py`)
* **Objetivo:** Registrar todas las herramientas (Calendar, Workouts, Tareas) con firmas tipadas para Tool Calling.
* **Dependencias:** Tareas 2.3, 3.2.
* **Entregables:** File `tools/registry.py`.
* **Criterios de Aceptación:** Catálogo centralizado de herramientas con esquemas JSON y docstrings detallados reconocibles por el LLM.

---

## 📍 Fase 4: Orquestación del LLM y Conexión con Telegram

### 🔹 Tarea 4.1 — Middleware de Autorización y Seguridad (`bot/handlers.py`)
* **Objetivo:** Bloquear interacciones no autorizadas en Telegram.
* **Dependencias:** Tarea 1.1.
* **Entregables:** Decorador/filtro de seguridad en `bot/handlers.py`.
* **Criterios de Aceptación:** Mensajes de usuarios con ID distinto a `TELEGRAM_USER_ID` son ignorados sin emitir respuesta.

### 🔹 Tarea 4.2 — Configuración del Motor del Agente (`agent/engine.py`)
* **Objetivo:** Construir el bucle de razonamiento y ejecución de herramientas con el LLM.
* **Dependencias:** Tarea 3.3.
* **Entregables:** File `agent/engine.py`.
* **Criterios de Aceptación:** El agente recibe mensajes, decide llamar a herramientas en `registry.py`, procesa los resultados y genera respuestas coherentes en lenguaje natural.

### 🔹 Tarea 4.3 — Diseño del System Prompt (`agent/prompts.py`)
* **Objetivo:** Definir las directrices de personalidad, fecha/hora y formato de respuesta del asistente.
* **Dependencias:** Tarea 4.2.
* **Entregables:** File `agent/prompts.py`.
* **Criterios de Aceptación:** Prompt probado; el bot responde de forma concisa, adaptada a pantallas móviles y consciente de la fecha/hora actual.

### 🔹 Tarea 4.4 — Enrutamiento de Mensajes y Comandos Rápidos
* **Objetivo:** Conectar el bot de Telegram con el motor del agente y crear comandos directos.
* **Dependencias:** Tareas 4.1 - 4.3.
* **Entregables:** Handlers de comandos (`/start`, `/hoy`, `/entreno`) y mensajes de texto en `bot/handlers.py`.
* **Criterios de Aceptación:** Respuesta inmediata tanto en lenguaje natural como mediante comandos slash.

---

## 📍 Fase 5: Programación Proactiva y Mensajería Automática

### 🔹 Tarea 5.1 — Integración de APScheduler en el Ciclo de Eventos
* **Objetivo:** Configurar el planificador de tareas asíncrono en el bucle principal.
* **Dependencias:** Tareas 1.4, 4.4.
* **Entregables:** Instancia de `AsyncIOScheduler` en `bot/scheduler.py`.
* **Criterios de Aceptación:** Scheduler inicializado correctamente dentro del bucle de eventos de `python-telegram-bot`.

### 🔹 Tarea 5.2 — Implementación del Briefing Matutino (Cron: 08:00 AM)
* **Objetivo:** Programar el consolidado automático diario de agenda, rutina y tareas.
* **Dependencias:** Tareas 2.3, 3.2, 5.1.
* **Entregables:** Función `send_morning_briefing()` en `bot/scheduler.py`.
* **Criterios de Aceptación:** Disparo puntual a las 08:00 AM con resumen completo sintetizado enviado al usuario por Telegram.

### 🔹 Tarea 5.3 — Implementación del Check-in Nocturno (Cron: 21:30 PM)
* **Objetivo:** Programar la notificación nocturna con botones interactivos Inline Keyboards.
* **Dependencias:** Tarea 5.1.
* **Entregables:** Función `send_nightly_checkin()` en `bot/scheduler.py`.
* **Criterios de Aceptación:** Disparo a las 21:30 PM adjuntando un teclado interactivo `InlineKeyboardMarkup`.

### 🔹 Tarea 5.4 — Manejador de Respuestas de Teclado (`CallbackQueryHandler`)
* **Objetivo:** Procesar los clics en los botones inline sin requerir escritura de texto.
* **Dependencias:** Tareas 2.3, 5.3.
* **Entregables:** CallbackHandler para botones inline en `bot/handlers.py`.
* **Criterios de Aceptación:** Pulsar un botón registra directamente el entreno o la tarea completada en la BD y actualiza el mensaje en Telegram.

---

## 📍 Fase 6: Empaquetado, Despliegue y Monitorización

### 🔹 Tarea 6.1 — Construcción del Dockerfile de Producción
* **Objetivo:** Crear una imagen Docker liviana y segura para la aplicación Python.
* **Dependencias:** Tarea 1.4.
* **Entregables:** File `Dockerfile`.
* **Criterios de Aceptación:** Construcción multi-etapa exitosa basada en `python:3.11-slim` con usuario no-root.

### 🔹 Tarea 6.2 — Orquestación Completa en Compose (`docker-compose.yml`)
* **Objetivo:** Integrar el bot y la base de datos PostgreSQL en un archivo compose unificado.
* **Dependencias:** Tareas 1.3, 6.1.
* **Entregables:** `docker-compose.yml` completo con servicio `bot`.
* **Criterios de Aceptación:** `docker compose up` levanta ambos servicios en el orden correcto y con montajes de volúmenes funcionales.

### 🔹 Tarea 6.3 — Despliegue en Servidor (VPS / Raspberry Pi)
* **Objetivo:** Desplegar el sistema en un entorno de servidor 24/7.
* **Dependencias:** Tarea 6.2.
* **Entregables:** Despliegue en producción funcional.
* **Criterios de Aceptación:** Contenedores ejecutándose de forma ininterrumpida con reinicio automático (`restart: unless-stopped`).

### 🔹 Tarea 6.4 — Sistema de Logs y Alertas de Fallos en Telegram
* **Objetivo:** Implementar rotación de logs y notificaciones automáticas ante errores no capturados.
* **Dependencias:** Tareas 4.1, 6.3.
* **Entregables:** Logger rotativo y manejador global de errores en Telegram.
* **Criterios de Aceptación:** Ante una falla crítica, el bot envía un mensaje con el traceback del error directamente al desarrollador en Telegram.
