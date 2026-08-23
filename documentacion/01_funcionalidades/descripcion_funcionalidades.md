# 📑 Especificación Completa de Funcionalidades (Prácticas y Técnicas)

Este documento detalla todas las capacidades que pretende desarrollar el **Telegram Personal AI Assistant**, divididas en la perspectiva práctica (experiencia de usuario en el día a día) y la perspectiva técnica (diseño de arquitectura, código e infraestructura).

---

## 🎯 1. Funcionalidades Prácticas (Perspectiva de Usuario)

### 🗓️ 1.1. Gestión Inteligente de Agenda y Calendario (Google Calendar)
* **Consulta en lenguaje natural:** El usuario puede preguntar por sus eventos ("¿Qué tengo que hacer hoy?", "¿Tengo reuniones el jueves por la mañana?").
* **Creación de eventos conversacional:** Permite programar nuevas citas simplemente redactando una instrucción ("Añade cena con Juan mañana a las 21:00").
* **Sincronización en tiempo real:** Todas las modificaciones se reflejan inmediatamente en la cuenta principal de Google Calendar del usuario.
* **Alertas ajustadas por zona horaria:** Manejo preciso de zonas horarias (`Europe/Madrid` por defecto) para prevenir solapamientos o desplazamientos de hora.

### 🏋️ 1.2. Control y Seguimiento Deportivo (Fitness & Rutinas)
* **Lógica de rotación automática:** El bot conoce la rutina secuencial (ej. Empuje ➔ Tirón ➔ Pierna ➔ Descanso). Al consultar el entrenamiento del día, evalúa automáticamente la última sesión realizada en la base de datos y sugiere la rutina que corresponde hoy.
* **Registro de métricas clave:** Posibilidad de registrar peso utilizado, repeticiones, nota técnica y RPE (*Rate of Perceived Exertion*, nivel de esfuerzo del 1 al 10).
* **Histórico determinista:** El usuario puede solicitar resúmenes de sus últimos entrenamientos o progresos de carga por ejercicio.

### 🧹 1.3. Gestión de Tareas Periódicas del Hogar y Recordatorios
* **Cálculo dinámico de vencimientos:** A diferencia de una alarma estática, el sistema calcula si una tarea recurrente (ej. *Limpiar filtros del aire*, *Revisar aceite del coche*, *Lavar cortinas*) está vencida midiendo el tiempo transcurrido desde la fecha real en que se marcó como completada por última vez.
* **Recordatorios puntuales rápidos:** Creación de recordatorios de un solo uso mediante lenguaje natural ("Recuérdame comprar pan a las 18:00").

### ⚡ 1.4. Automatización Proactiva y Notificaciones Bidireccionales
* **Briefing Matutino (08:00 AM):** Envío automático diario de un resumen consolidado conteniendo:
  1. Eventos y citas del calendario programados para hoy.
  2. La rutina de entrenamiento que toca ejecutar.
  3. Las tareas periódicas que vencen en el día.
* **Check-in Nocturno Interactivo (21:30 PM):** Notificación proactiva nocturna acompañada de botones interactivos de Telegram (*Inline Keyboards*):
  - `[✅ Entreno Hecho]`
  - `[💤 Día de Descanso]`
  - `[🧹 Tareas Completadas]`
  El usuario puede marcar sus hábitos diarios con un solo toque en pantalla sin necesidad de escribir texto.

### 🔒 1.5. Aislamiento y Privacidad Personal
* **Acceso Restringido:** El sistema es un asistente privado 1:1. Cualquier intento de interacción procedente de un ID de Telegram no autorizado es bloqueado en silencio sin procesar comandos ni gastar créditos de APIs.

---

## 🛠️ 2. Funcionalidades Técnicas (Perspectiva de Ingeniería)

### 🧠 2.1. Motor del Agente LLM y Tool Calling
* **Extracción de intenciones y parámetros:** Integración con modelos LLM (OpenAI / Gemini / Anthropic) mediante API con soporte nativo de **Tool / Function Calling**.
* **Ejecución determinista:** El LLM no inventa ni simula datos: cuando detecta una intención operativa, emite una llamada a una herramienta registrada (`registry.py`), la cual ejecuta código Python contra la base de datos o la API de Google.
* **Bucle de Razonamiento (Agent Loop):**  
  `User Prompt` ➔ `LLM Decision` ➔ `Tool Execution` ➔ `LLM Context Injection` ➔ `Final Natural Language Response`.

### 🛡️ 2.2. Middleware de Seguridad e Intercepción
* **Filtro Middleware a nivel de Bot:** Interceptor nativo en `python-telegram-bot` que evalúa `update.effective_user.id == TELEGRAM_USER_ID`. Si la condición es falsa, se interrumpe inmediatamente el pipeline del manejador.

### 💾 2.3. Persistencia Relacional Asíncrona (PostgreSQL + SQLAlchemy Async)
* **Motor Asíncrono con `asyncpg`:** Conexión de alto rendimiento basada en `asyncio` evadiendo bloqueos de I/O en el event loop.
* **Modelado ORM Declarativo:** Tablas normalizadas en `database/models.py` (`workouts`, `workout_logs`, `recurring_tasks`, `quick_reminders`).
* **Patrón CRUD Determinista:** Funciones asíncronas puras encapsuladas en `database/crud.py` invocadas de forma segura desde las herramientas del agente.

### 🌐 2.4. Integración OAuth2 y cliente Google Calendar API
* **Persistencia de Tokens OAuth2:** Flujo de autenticación capaz de refrescar tokens expirados (`google_token.json`) de forma transparente sin requerir re-autorización constante por navegador.
* **Formateo ISO 8601:** Conversión de fechas y horarios entre lenguaje natural, formatos ISO y zonas horarias usando `pytz` / `zoneinfo`.

### ⏱️ 2.5. Programación de Tareas Proactivas (`APScheduler`)
* **Integración en Event Loop Asíncrono:** Utilización de `AsyncIOScheduler` compartiendo el mismo ciclo de eventos (`asyncio loop`) que el bot de Telegram.
* **Disparadores Cron:** Configuración de tareas recurrentes para envío automático del Briefing (08:00 AM) y Check-in nocturno (21:30 PM).

### ⚙️ 2.6. Configuración y Validación de Entorno con Pydantic
* **`Pydantic Settings`:** Carga y validación estricta de tipos de las variables de entorno (`.env`) al iniciar la aplicación, deteniendo el arranque de inmediato si falta alguna clave requerida (`TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, API Keys).

### 🐳 2.7. Contenedorización Multi-etapa y Orquestación Docker
* **Dockerfile Multi-stage:** Imagen optimizada basada en `python:3.11-slim` sin dependencias de compilación redundantes en la etapa final y ejecutada con usuario sin privilegios root.
* **Docker Compose Orquestado:** Gestión coordinada de los servicios `db` (PostgreSQL 16) y `bot`, con *healthchecks* para garantizar que el bot no inicie hasta que la base de datos esté lista para recibir conexiones.

### 🚨 2.8. Observabilidad, Logging y Notificaciones de Excepción
* **Logs Rotativos:** Módulo de `logging` en Python configurado con rotación de archivos para evitar llenar el disco.
* **Alertas de Traceback en Telegram:** Capturador global de excepciones no controladas que reenvía el informe del error y el traceback detallado directamente al chat de Telegram del usuario.
