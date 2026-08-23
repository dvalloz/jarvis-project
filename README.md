# 🤖 Jarvis - Asistente Personal Inteligente en Telegram

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram_Bot_API-v21-blue.svg)
![Groq API](https://img.shields.io/badge/Groq_API-Qwen_27B-orange.svg)
![APScheduler](https://img.shields.io/badge/APScheduler-AsyncIO-green.svg)
![Docker](https://img.shields.io/badge/Docker_Compose-Ready-blue.svg)

> **Jarvis** es el asistente personal proactivo, inteligente y adaptable de David integrado en Telegram. Gestiona automáticamente tu agenda de Google Calendar, rutinas adaptativas de gimnasio y escalada, recordatorios de salud (toma y consulta de pastilla), control de cobros compartidos (Spotify Bizum), asistencia a la oficina y seguimiento proactivo aislado de tareas con fecha límite (*deadlines*) con notificaciones de cuenta atrás y botones táctiles de borrado instantáneo.

---

## 🏗️ 1. Arquitectura General del Sistema

El sistema está diseñado bajo una arquitectura en capas desacopladas de 5 niveles, operada de forma asíncrona sobre el bucle de eventos (`asyncio`) de Python:

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                         CAPA 1: ENTRADAS / INTERFAZ                    │
 │    Mensaje Telegram / Comandos / Botones Inline / Temporizadores Cron │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      CAPA 2: SEGURIDAD Y ENRUTADO                      │
 │    Middleware @restricted (Filtra por TELEGRAM_USER_ID en bot/handlers)│
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                 CAPA 3: ORQUESTACIÓN Y PROMPT SYSTEM                   │
 │   agent/prompts.py (Contexto temporal + Inferencia de Contexto)        │
 │   agent/engine.py  (Cliente Groq/OpenAI + Modelo Qwen 27B)             │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ (Tool Calling / XML Fallback)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                 CAPA 4: CATÁLOGO Y HERRAMIENTAS (TOOLS)                │
 │   tools/registry.py (15 esquemas JSON reconocidos por el LLM)          │
 │   tools/workout_tools.py | tools/task_tools.py                        │
 └─────────────────┬──────────────────────────────────┬───────────────────┘
                   │                                  │
                   ▼                                  ▼
 ┌───────────────────────────────────┐  ┌─────────────────────────────────┐
 │   CAPA 5A: INTEGRACIÓN EXTERNA    │  │   PostgreSQL 16 via SQLAlchemy  │
 │   Google Calendar API (OAuth2)    │  │   database/models.py & crud.py  │
 │   tools/calendar_tools.py         │  │                                 │
 └───────────────────────────────────┘  └─────────────────────────────────┘
```

---

## 🔄 2. ¿Cómo Funciona a Nivel Técnico? (Flujos de Ejecución)

### 💬 Flujo A: Interacción por Chat (Mensaje del Usuario)
1. **Recepción y Filtrado:** [bot/handlers.py](file:///c:/Users/dvdva/Documents/jarvis-project/bot/handlers.py) intercepta el evento. El decorador `@restricted` verifica que el ID de usuario coincida exactamente con `settings.telegram_user_id`.
2. **Acción Visual:** Se activa la indicación *"escribiendo..."* (*typing chat action*) en Telegram.
3. **Construcción del Contexto:** `run_agent()` en [agent/engine.py](file:///c:/Users/dvdva/Documents/jarvis-project/agent/engine.py) solicita el System Prompt dinámico a [agent/prompts.py](file:///c:/Users/dvdva/Documents/jarvis-project/agent/prompts.py), que calcula en tiempo real la fecha, día de la semana, hora local y zona horaria (`Europe/Madrid`).
4. **Primera Llamada al LLM:** Petición a Groq API (`qwen/qwen3.6-27b`) pasando la lista de herramientas en `TOOLS_SCHEMA` ([tools/registry.py](file:///c:/Users/dvdva/Documents/jarvis-project/tools/registry.py)).
5. **Ejecución de Herramientas (Tool Calling Loop & XML Fallback):**
   - El motor ejecuta la herramienta correspondiente (`get_calendar_events`, `get_next_workout`, `log_climbing_activity`, `check_pill_status`, `confirm_pill_taken`, `get_pending_deadline_tasks`, `update_spotify_bizum`, etc.).
   - Se realizan las lecturas o mutaciones asíncronas en la base de datos PostgreSQL vía [database/crud.py](file:///c:/Users/dvdva/Documents/jarvis-project/database/crud.py) o consultas a la API de Google Calendar.
6. **Síntesis y Respuesta:** El motor reenvía los resultados de las herramientas al LLM para redactar una respuesta natural con emojis y formato en castellano. `safe_reply_text()` entrega el mensaje en Telegram adjuntando teclados táctiles interactivos de forma dinámica.

### ⏰ Flujo B: Disparos Automáticos Proactivos (Parrilla de Crons y Chequeo Periódico)
El motor [bot/scheduler.py](file:///c:/Users/dvdva/Documents/jarvis-project/bot/scheduler.py) ejecuta tareas programadas sin necesidad de intervención manual:

| Frecuencia / Hora | Tarea | Descripción / Acción |
| :--- | :--- | :--- |
| **Cada 15 min** | **Deadline Checker** | **Avisos aislados e independientes de tareas con fecha límite.** Envía notificaciones de cuenta atrás (a las 24h, 6h, 3h, 1h o al vencer) con botón `[✅ Marcar como hecha]`. |
| **07:30 AM** | **Morning Briefing** | Lunes: Agenda completa de la semana (Mon-Sun). Martes-Domingo: Agenda del día + recordatorio de pastilla + lista de tareas pendientes con botones táctiles. |
| **15:00 PM** | **Pill 2nd Check** | Verifica si la pastilla fue tomada. Si no ha sido confirmada, envía el segundo aviso. |
| **20:00 PM** | **Gym Reminder** | (Lunes a Viernes) Propone la rutina de entrenamiento adaptativa según el descanso de escalada y rotación. |
| **21:00 PM** | **Nightly Checks** | 3er aviso de pastilla + recordatorio nocturno de oficina + Bizum Spotify (días 16+, cada 2 días) + Resumen Mensual de Entrenamientos el último día del mes. |
| **22:00 PM** | **Gym Check-in** | (Lunes a Viernes) Muestra el teclado inline (`[✅ Entreno Hecho]`, `[🧗 Fui a Escalada]`, `[💤 Día de Descanso]`). |

---

## 📂 3. Desglose Estructurado del Código por Archivos

| Módulo / Archivo | Función y Responsabilidad Técnica |
| :--- | :--- |
| [main.py](file:///c:/Users/dvdva/Documents/jarvis-project/main.py) | Punto de entrada principal. Inicializa PostgreSQL, registra handlers, inicia APScheduler en el event loop y ejecuta `run_polling()`. |
| [Dockerfile](file:///c:/Users/dvdva/Documents/jarvis-project/Dockerfile) | Configuración de la imagen Docker de producción (Python 3.12-slim, zona horaria Europe/Madrid y optimización de capas). |
| [docker-compose.yml](file:///c:/Users/dvdva/Documents/jarvis-project/docker-compose.yml) | Definición de servicios para Docker Compose (PostgreSQL 16 `db` + Aplicación `bot` con comprobación de salud). |
| [config/settings.py](file:///c:/Users/dvdva/Documents/jarvis-project/config/settings.py) | Singleton Pydantic BaseSettings. Valida variables de entorno `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_USER_ID`, `GROQ_API_KEY`, etc.). |
| [database/connection.py](file:///c:/Users/dvdva/Documents/jarvis-project/database/connection.py) | Configuración del motor asíncrono `create_async_engine` con `asyncpg` y fábrica `AsyncSessionLocal`. |
| [database/models.py](file:///c:/Users/dvdva/Documents/jarvis-project/database/models.py) | Modelos ORM SQLAlchemy (`Workout`, `WorkoutLog`, `PillLog`, `SpotifyPaymentTracker`, `OfficeSchedule`, `DeadlineTask`). |
| [database/crud.py](file:///c:/Users/dvdva/Documents/jarvis-project/database/crud.py) | Funciones de consulta y mutación en BD, algoritmo adaptativo de rutinas, gestión de tareas y actualización de avisos aislados. |
| [database/seed.py](file:///c:/Users/dvdva/Documents/jarvis-project/database/seed.py) | Inicializador de base de datos. Crea tablas e inserta rutinas base (*Push, Pull, Pierna, Escalada, Full-Body, Cardio*). |
| [tools/registry.py](file:///c:/Users/dvdva/Documents/jarvis-project/tools/registry.py) | Catálogo de 15 esquemas JSON de herramientas expuestas al LLM. |
| [tools/calendar_tools.py](file:///c:/Users/dvdva/Documents/jarvis-project/tools/calendar_tools.py) | Cliente OAuth2 de Google Calendar (`get_day_events`, `get_week_events`, `create_calendar_event`). |
| [tools/workout_tools.py](file:///c:/Users/dvdva/Documents/jarvis-project/tools/workout_tools.py) | Wrappers de herramientas para rutinas sugeridas, escalada y resumen mensual. |
| [tools/task_tools.py](file:///c:/Users/dvdva/Documents/jarvis-project/tools/task_tools.py) | Wrappers de herramientas para toma/consulta de pastilla, Spotify, oficina, creación/modificación/borrado de *deadlines*. |
| [agent/prompts.py](file:///c:/Users/dvdva/Documents/jarvis-project/agent/prompts.py) | Generador de System Prompt personalizado para David con reglas en castellano y lógica de inferencia. |
| [agent/engine.py](file:///c:/Users/dvdva/Documents/jarvis-project/agent/engine.py) | Bucle de razonamiento asíncrono Groq/OpenAI, ejecutor de herramientas y limpiador de etiquetas `<think>`. |
| [bot/handlers.py](file:///c:/Users/dvdva/Documents/jarvis-project/bot/handlers.py) | Decorador de seguridad `@restricted`, comandos (`/start`, `/hoy`, `/entreno`), procesador de texto, Callbacks inline y borrado de tareas. |
| [bot/scheduler.py](file:///c:/Users/dvdva/Documents/jarvis-project/bot/scheduler.py) | Motor `AsyncIOScheduler` que orquesta la parrilla proactiva y el chequeador aislado de tareas con fecha límite cada 15 minutos. |
| [auth_google.py](file:///c:/Users/dvdva/Documents/jarvis-project/auth_google.py) | Script auxiliar para realizar la primera autenticación OAuth2 de Google Calendar de forma interactiva. |

---

## 🧮 4. Algoritmos y Reglas Clave Implementadas

1. **Rotación Adaptativa de Rutinas (`get_smart_next_workout_routine`):**
   $$\text{Filtro Semanal} \rightarrow \text{Verificación de Escalada} \rightarrow \text{Rotación Clásica (Push ➡️ Pull ➡️ Pierna)}$$
   - Si durante la semana (Lunes a Domingo) ya completaste *Push*, *Pull* y *Pierna*, sugiere *Full-Body* o *Cardio*.
   - Si tu última sesión registrada fue *Escalada*, descarta automáticamente *Pull* al día siguiente para no sobrecargar flexores y espalda, sugiriendo *Pierna* o *Push*.
2. **Detección Automática de Fin de Mes:**
   - Evalúa `(today + timedelta(days=1)).month != today.month` para enviar el resumen de entrenamientos el último día del mes (funciona en meses de 28, 30 o 31 días).
3. **Inferencia de Contexto en Lenguaje Natural:**
   - Si escribes *"Mañana voy a la oficina"*, el motor ejecuta `set_office_attendance(will_attend=True)`. El martes, al comprobar la BD, detecta la respuesta previa y no te vuelve a hacer la pregunta proactiva.
4. **Recordatorio Periódico Aislado y Borrado de *Deadlines*:**
   - Cuando registras una tarea puntual (ej. *"Pedir cita en el taller antes del viernes a las 18:00"*), el chequeador en segundo plano evalúa la cuenta atrás y envía notificaciones aisladas por Telegram (ej. a 5h, 2h, 1h) con el botón táctil `[✅ Marcar como hecha]`.
   - Al pulsar el botón o confirmarla por chat, la tarea se **elimina permanentemente de la base de datos PostgreSQL**.

---

## 🚀 5. Guía Completa de Despliegue con Docker (Servidor Linux / Windows)

A continuación se detallan todos los pasos y comandos necesarios para construir la imagen de Docker y poner a funcionar el bot en cualquier servidor o máquina local.

---

### 🔑 Paso 1: Obtención de Claves y Credenciales

1. **Telegram Bot Token:**
   - En Telegram, habla con `@BotFather`.
   - Envía `/newbot`, asigna nombre y usuario a tu bot.
   - Copia el Token generado (ej. `8900005608:AAEg8tty...`).
2. **Telegram User ID:**
   - En Telegram, habla con `@userinfobot`.
   - Copia tu ID numérico (ej. `7246760773`).
3. **Groq API Key (100% Gratuito):**
   - Entra en [console.groq.com](https://console.groq.com/) y regístrate.
   - Ve a **API Keys** ➡️ **Create API Key** y copia la clave (empieza por `gsk_...`).
4. **Google Calendar OAuth Credentials (`google_credentials.json`):**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/).
   - Crea un proyecto ➡️ Habilita **Google Calendar API**.
   - Configura la **Pantalla de Consentimiento OAuth** (*OAuth Consent Screen*) en estado *Testing* y añade tu correo Gmail en **Test Users**.
   - En **Credenciales** ➡️ **Crear credenciales** ➡️ **ID de cliente OAuth** ➡️ Tipo *Aplicación de escritorio*.
   - Descarga el archivo JSON y guárdalo como `credentials/google_credentials.json` en la raíz del proyecto.

---

### 📦 Paso 2: Creación de la Imagen Docker y Contenedores

#### 🛠️ Método Recomendado: Despliegue con Docker Compose (Pila Completa 24/7)

Docker Compose levantará automáticamente tanto la Base de Datos PostgreSQL 16 como el contenedor de la aplicación Jarvis, encargándose de sincronizar la salud de la red interna:

##### En Linux (Servidor VPS / Ubuntu / Debian)
```bash
# 1. Actualizar e instalar Docker + Docker Compose
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose-v2
sudo systemctl enable --now docker

# 2. Clonar el repositorio
git clone <URL_DE_TU_REPOSITORIO> jarvis-project
cd jarvis-project

# 3. Crear el archivo de configuración .env
cat <<EOF > .env
TELEGRAM_BOT_TOKEN="tu_telegram_bot_token"
TELEGRAM_USER_ID=tu_telegram_user_id_numerico

POSTGRES_USER=jarvis_user
POSTGRES_PASSWORD=jarvis_password
POSTGRES_DB=jarvis_db
DATABASE_URL=postgresql+asyncpg://jarvis_user:jarvis_password@db:5432/jarvis_db

GROQ_API_KEY=gsk_tu_groq_api_key
OPENAI_API_KEY=sk-placeholder-key
TIMEZONE=Europe/Madrid
EOF

# 4. Asegurar que las credenciales de Google están en la carpeta credentials/
mkdir -p credentials
# Copia google_credentials.json y google_token.json a credentials/

# 5. Construir la imagen e iniciar los contenedores en segundo plano (daemon)
docker compose up -d --build
```

##### En Windows (PowerShell / Docker Desktop)
```powershell
# 1. Clonar el repositorio y entrar en la carpeta
git clone <URL_DE_TU_REPOSITORIO> jarvis-project
cd jarvis-project

# 2. Crear el archivo .env con tus claves
# (Asegúrate de colocar tu TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID y GROQ_API_KEY)

# 3. Construir la imagen y levantar todo en segundo plano
docker compose up -d --build
```

---

#### 🔨 Método Manual: Construir la Imagen de Docker (*docker build*)

Si prefieres construir la imagen del bot de forma independiente y ejecutarla manualmente:

```bash
# 1. Construir la imagen de Docker a partir del Dockerfile
docker build -t jarvis-bot:latest .

# 2. Verificar que la imagen se ha creado correctamente
docker images
```

Para ejecutar el contenedor de la imagen creada conectándolo a la base de datos:
```bash
docker run -d \
  --name jarvis_bot_container \
  --restart always \
  --env-file .env \
  -v $(pwd)/credentials:/app/credentials \
  jarvis-bot:latest
```

---

### 🛠️ Paso 3: Comandos Útiles de Mantenimiento y Logs

- **Ver logs en tiempo real del Bot en Docker:**
  ```bash
  docker compose logs -f bot
  ```
- **Ver logs de la Base de Datos:**
  ```bash
  docker compose logs -f db
  ```
- **Ver el estado de los contenedores:**
  ```bash
  docker compose ps
  ```
- **Detener los servicios:**
  ```bash
  docker compose down
  ```
- **Reiniciar los servicios:**
  ```bash
  docker compose restart
  ```
- **Hacer un Backup (Copia de seguridad) de PostgreSQL:**
  ```bash
  docker exec -t jarvis_postgres_db pg_dump -U jarvis_user jarvis_db > backup_jarvis.sql
  ```
- **Restaurar un Backup en PostgreSQL:**
  ```bash
  docker exec -i jarvis_postgres_db psql -U jarvis_user jarvis_db < backup_jarvis.sql
  ```