# 🤖 Telegram Personal AI Assistant: Fitness, Calendar & Task Manager

## 📖 1. Descripción Detallada del Proyecto

El objetivo principal de este proyecto es el diseño, desarrollo y despliegue de un **asistente personal inteligente y proactivo** accesible exclusivamente a través de un chat privado de **Telegram**. El sistema integra un modelo de lenguaje de última generación (LLM) con bases de datos relacionales, APIs externas de productividad y un motor de tareas programadas (scheduler), funcionando 24/7 en un entorno contenedorizado.

A diferencia de un chatbot conversacional estándar, este agente no se limita a responder preguntas: cuenta con capacidades de **Tool / Function Calling**, lo que le permite ejecutar operaciones de lectura y escritura sobre diferentes dominios de la vida diaria del usuario, combinando determinismo lógico con procesamiento de lenguaje natural.

### 🎯 Dominios de Gestión del Agente:

1. **🗓️ Gestión de Agenda y Calendario (Google Calendar):**
   * Lectura de los eventos de mi Google Calendar.
   * Lectura de los eventos del calendario a principio del dia y conforme se vaya acercando el evento
   

2. **🏋️ Control y Seguimiento de Entrenamientos:**
   * Almacenamiento determinista del plan de entrenamiento (rotaciones de rutinas como Empuje / Tirón / Pierna, días de descanso, etc.).
   * Registro histórico de sesiones completadas y cargas.
   * Lógica automática de rotación: el bot sabe exactamente qué rutina toca hoy en función de cuándo y qué se entrenó en la última sesión.
   * A final de cada semana y cada mes me dara un resumen de los entrenamientos realizados duarante el periodo.

3. **🧹 Gestión de Tareas Periódicas y del Hogar:**
   * Seguimiento de tareas de mantenimiento recurrente (semanales, mensuales o por intervalos de días), tales como limpieza de filtros, mantenimiento del coche o coladas.
   * Cálculo dinámico de vencimientos: solo alerta de una tarea cuando ha transcurrido el intervalo configurado desde su último cumplimiento.
   * Registro rápido de tareas puntuales y recordatorios del día.

4. **⚡ Automatización y Proactividad (Notificaciones Bidireccionales):**
   * **Briefing Matutino:** Generación y envío automático a primera hora del día de un informe consolidado con los eventos del calendario, la rutina de gimnasio correspondiente y las tareas pendientes.
   * **Check-in Nocturno Interactivo:** Envío de recordatorio nocturno con teclados interactivos (*Inline Keyboards*) para marcar entrenamientos y tareas completadas con un solo clic, sin fricción de escritura.

5. **🔒 Seguridad y Aislamiento:**
   * Control de acceso estricto a nivel de middleware: el bot ignora y bloquea cualquier solicitud que no provenga del ID de usuario autorizado.

---

## 🛠️ 2. Stack Tecnológico

| Capa | Tecnología | Función |
|---|---|---|
| **Lenguaje Base** | `Python 3.11+` | Desarrollo asíncrono con tipado estático y compatibilidad de librerías. |
| **Interfaz de Usuario** | `python-telegram-bot` (v21+) | Gestión de eventos, comandos, mensajes y teclados interactivos en Telegram. |
| **Cerebro / LLM** | `OpenAI` / `Gemini` / `Anthropic` API | Razonamiento, extracción de intenciones y ejecución de herramientas (*Tool Calling*). |
| **Base de Datos** | `PostgreSQL 16` + `SQLAlchemy (Async)` | Persistencia relacional de rutinas, historial de entrenos y tareas periódicas. |
| **Driver de BD** | `asyncpg` | Conexión asíncrona de alto rendimiento a PostgreSQL. |
| **Integración Externa** | `Google Calendar API` (`google-api-python-client`) | Sincronización bidireccional de eventos y citas vía OAuth2. |
| **Planificador** | `APScheduler` (`AsyncIOScheduler`) | Ejecución de crons y disparadores proactivos en el event loop. |
| **Validación de Datos** | `Pydantic` / `Pydantic-Settings` | Gestión y validación de esquemas de datos y variables de entorno. |
| **Despliegue** | `Docker` & `Docker Compose` | Aislamiento, persistencia de volúmenes y despliegue continuo en VPS/Servidor. |

---

## 📁 3. Estructura del Repositorio

```text
telegram-ai-assistant/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── credentials/
│   ├── google_credentials.json
│   └── google_token.json
├── config/
│   └── settings.py
├── database/
│   ├── connection.py
│   ├── models.py
│   ├── crud.py
│   └── seed.py
├── tools/
│   ├── calendar_tools.py
│   ├── workout_tools.py
│   ├── task_tools.py
│   └── registry.py
├── agent/
│   ├── prompts.py
│   └── engine.py
├── bot/
│   ├── handlers.py
│   └── scheduler.py
└── main.py
```

---

## 🚀 4. Plan de Implementación por Fases

### 📍 Fase 1: Configuración de Infraestructura, Accesos y Entorno

#### 🔹 Tarea 1.1 — Creación y securización del Bot de Telegram
- Habla con [@BotFather](https://t.me/BotFather) en Telegram para generar el bot y obtener el `TELEGRAM_BOT_TOKEN`.
- Desactiva la opción de añadir el bot a grupos (`/setjoingroups` ➔ `Disable`).
- Utiliza `@userinfobot` para obtener tu `TELEGRAM_USER_ID` numérico personal, el cual servirá de filtro estricto de seguridad.

#### 🔹 Tarea 1.2 — Configuración de Google Cloud y OAuth2
- Crea un proyecto en **Google Cloud Console**, habilita la **Google Calendar API** y configura la pantalla de consentimiento OAuth en modo *External / Testing*, añadiendo tu correo como usuario de prueba.
- Crea credenciales de tipo **OAuth Client ID** (*Desktop Application*) y descarga el archivo como `credentials/google_credentials.json`.

#### 🔹 Tarea 1.3 — Infraestructura de persistencia con Docker Compose
- Escribe el archivo `docker-compose.yml` declarando un contenedor para **PostgreSQL 16** con volumen persistente local (`postgres_data:/var/lib/postgresql/data`), mapeo de puertos y red interna aislada.

#### 🔹 Tarea 1.4 — Gestión de dependencias y configuración centralizada
- Define `requirements.txt` (`python-telegram-bot`, `sqlalchemy`, `asyncpg`, `pydantic-settings`, `google-api-python-client`, `google-auth-oauthlib`, `apscheduler`, SDK de LLM).
- Implementa `config/settings.py` con **Pydantic** para validar automáticamente la presencia de todas las claves y rutas de entorno al arrancar la app.

---

### 📍 Fase 2: Modelado de Datos y Capa de Persistencia

#### 🔹 Tarea 2.1 — Definición de esquemas ORM (`database/models.py`)
Modela las tablas en SQLAlchemy asíncrono:
- **`workouts`**: Catálogo de rutinas con orden secuencial (`id`, `name`, `order_index`, `target_muscles`, `description`).
- **`workout_logs`**: Historial de ejecuciones (`id`, `workout_id`, `completed_at`, `notes`, `rpe`).
- **`recurring_tasks`**: Tareas periódicas (`id`, `title`, `frequency_type` [*días/mensual/semanal*], `interval_value`, `last_completed_at`, `is_active`).
- **`quick_reminders`**: Recordatorios puntuales (`id`, `text`, `due_date`, `is_done`).

#### 🔹 Tarea 2.2 — Conexión y sesión asíncrona (`database/connection.py`)
- Configura el `async_engine` y `async_sessionmaker` usando el driver `asyncpg`.
- Asegura la gestión de conexiones mediante context managers (`async with get_db() as session:`).

#### 🔹 Tarea 2.3 — Implementación de operaciones CRUD (`database/crud.py`)
Escribe funciones asíncronas deterministas:
- `get_next_workout_routine()`: Determina la rutina correspondiente según el último registro en `workout_logs` y el `order_index`.
- `log_completed_workout()`: Inserta el registro del entreno y actualiza marcas temporales.
- `get_due_recurring_tasks()`: Filtra tareas cuya última fecha de ejecución más el intervalo sea menor o igual a la fecha actual.
- `mark_task_completed()`: Actualiza `last_completed_at` a la fecha en curso.

#### 🔹 Tarea 2.4 — Script de inicialización y sembrado (`database/seed.py`)
- Crea un script independiente para crear las tablas en la BD y poblar los datos iniciales con tu rotación de entrenamientos y las tareas recurrentes del hogar.

---

### 📍 Fase 3: Integraciones Externas y Herramientas del Agente (Tools)

#### 🔹 Tarea 3.1 — Autenticación y cliente de Google Calendar (`tools/calendar_tools.py`)
- Implementa la lógica de autenticación OAuth2 que cargue `google_token.json` si existe, o abra el flujo de autorización inicial mediante navegador para generarlo y persistirlo localmente.

#### 🔹 Tarea 3.2 — Métodos operativos de Calendar
Desarrolla las funciones:
- `get_day_events(target_date)`: Recupera eventos comprendidos entre las `00:00:00` y las `23:59:59` en la zona horaria local (`Europe/Madrid`), extrayendo título, hora de inicio/fin y descripción.
- `create_calendar_event(summary, start_iso, end_iso, description)`: Inserta eventos directamente en el calendario primario.

#### 🔹 Tarea 3.3 — Envoltorios de herramientas para el LLM (`tools/registry.py`)
- Empaqueta las funciones de Calendar, Workouts y Tareas bajo firmas tipadas compatibles con **Tool Calling**, incluyendo descripciones detalladas de los parámetros para que el modelo decida cuándo y cómo ejecutarlas.

---

### 📍 Fase 4: Orquestación del LLM y Conexión con Telegram

#### 🔹 Tarea 4.1 — Middleware de autorización y seguridad (`bot/handlers.py`)
- Crea un decorador o filtro nativo para `python-telegram-bot` que intercepte todos los mensajes y descarte silenciosamente cualquier interacción cuyo `update.effective_user.id` no coincida con `TELEGRAM_USER_ID`.

#### 🔹 Tarea 4.2 — Configuración del motor del agente (`agent/engine.py`)
- Configura la llamada al LLM con soporte de **Tool Calling**.
- Implementa el bucle de ejecución:  
  `Entrada del usuario` ➔ `Invocación LLM` ➔ `Ejecución de herramientas` ➔ `Output a LLM` ➔ `Respuesta final en lenguaje natural`.

#### 🔹 Tarea 4.3 — Diseño del System Prompt (`agent/prompts.py`)
- Escribe el prompt maestro fijando la personalidad: asistente personal proactivo, conciso y directo, con conocimiento explícito de la fecha/hora actual, zona horaria y pautas de formato aptas para lectura rápida en móvil.

#### 🔹 Tarea 4.4 — Enrutamiento de mensajes y comandos
- Vincula el `MessageHandler(filters.TEXT & ~filters.COMMAND)` para procesar lenguaje natural a través del agente.
- Crea comandos rápidos como `/start`, `/hoy` o `/entreno` para consultas directas sin pasar por el LLM.

---

### 📍 Fase 5: Programación Proactiva y Mensajería Automática

#### 🔹 Tarea 5.1 — Integración de APScheduler en el ciclo de eventos
- Inicializa `AsyncIOScheduler` dentro de la función de arranque del bot, asegurando que comparta el mismo bucle de eventos (*asyncio event loop*) que `python-telegram-bot`.

#### 🔹 Tarea 5.2 — Implementación del Briefing Matutino (Cron: 08:00 AM)
- Crea una tarea programada que recopile:
  1. Eventos del día de Google Calendar.
  2. La rutina de entrenamiento que toca hoy.
  3. Tareas periódicas que vencen hoy.
- El LLM sintetiza estos datos en un único mensaje estructurado y lo envía vía `bot.send_message`.

#### 🔹 Tarea 5.3 — Implementación del Check-in Nocturno (Cron: 21:30 PM)
- Crea una tarea programada nocturna que envíe un mensaje preguntando por el estado del día acompañado de un teclado interactivo (`InlineKeyboardMarkup`):  
  `[✅ Entreno Hecho]` `[💤 Día de Descanso]` `[🧹 Tareas Listas]`.

#### 🔹 Tarea 5.4 — Manejador de respuestas de teclado (`CallbackQueryHandler`)
- Implementa la lógica para capturar los clics en los botones inline, ejecutando `log_completed_workout()` o `mark_task_completed()` de forma directa sin requerir que escribas texto.

---

### 📍 Fase 6: Empaquetado, Despliegue y Monitorización

#### 🔹 Tarea 6.1 — Construcción del Dockerfile de producción
- Crea un `Dockerfile` multi-etapa basado en `python:3.11-slim`, instalando dependencias sin caché y configurando un usuario no-root para ejecución segura.

#### 🔹 Tarea 6.2 — Orquestación completa en Compose (`docker-compose.yml`)
- Añade el servicio `bot` junto al de PostgreSQL, definiendo dependencia (`depends_on: db: condition: service_healthy`), políticas de reinicio (`restart: unless-stopped`) y montajes de volúmenes para `/credentials` y `/logs`.

#### 🔹 Tarea 6.3 — Despliegue en servidor (VPS / Raspberry Pi)
- Clona el repositorio en la máquina de destino, ejecuta la autenticación inicial para generar el `google_token.json`, levanta los servicios con `docker compose up -d` y comprueba la persistencia de datos mediante reinicios simulados.

#### 🔹 Tarea 6.4 — Sistema de logs y alertas de fallos
- Configura el módulo estándar `logging` con rotación de ficheros y añade un capturador global de errores en el bot para que, si una herramienta o llamada a la API falla, te envíe una alerta con el traceback directamente a Telegram.
