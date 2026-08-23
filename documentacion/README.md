# 📚 Documentación Oficial del Proyecto: Telegram Personal AI Assistant

Bienvenido al centro de documentación técnica y funcional de **Telegram Personal AI Assistant** (Fitness, Calendar & Task Manager). Este repositorio de documentación contiene todas las especificaciones, diagramas de arquitectura, desgloses de fases y guías de ejecución paso a paso para desarrollar y desplegar el proyecto.

---

## 🗺️ Mapa de Navegación de la Documentación

### 1. 📖 [01_funcionalidades/descripcion_funcionalidades.md](./01_funcionalidades/descripcion_funcionalidades.md)
* **Funcionalidades Prácticas:** Visión de usuario (Google Calendar, rutina de entrenamientos RPE, tareas recurrentes del hogar, Briefings matutinos, Check-ins nocturnos interactivos).
* **Funcionalidades Técnicas:** Visión de arquitectura e ingeniería (Tool Calling LLM, middleware de seguridad por User ID, persistencia PostgreSQL async, OAuth2, APScheduler, Docker).

### 2. 📋 [02_fases_y_tareas/desglose_fases_tareas.md](./02_fases_y_tareas/desglose_fases_tareas.md)
* Desglose completo del ciclo de vida del proyecto en **6 Fases** y **20 Tareas**.
* Matriz de objetivos, dependencias técnicas, entregables y criterios de aceptación por tarea.

### 3. 🚀 Planes de Ejecución por Fase (`03_plan_ejecucion/`)

#### 📍 [Fase 1: Configuración de Infraestructura, Accesos y Entorno](./03_plan_ejecucion/01_fase_infraestructura/resumen_fase.md)
* 🔹 [Tarea 1.1 — Creación y Securización del Bot de Telegram](./03_plan_ejecucion/01_fase_infraestructura/tarea_1_1_bot_telegram.md)
* 🔹 [Tarea 1.2 — Configuración de Google Cloud y OAuth2](./03_plan_ejecucion/01_fase_infraestructura/tarea_1_2_google_oauth.md)
* 🔹 [Tarea 1.3 — Infraestructura de Persistencia con Docker Compose](./03_plan_ejecucion/01_fase_infraestructura/tarea_1_3_docker_compose.md)
* 🔹 [Tarea 1.4 — Gestión de Dependencias y Configuración Centralizada](./03_plan_ejecucion/01_fase_infraestructura/tarea_1_4_settings_pydantic.md)

#### 📍 [Fase 2: Modelado de Datos y Capa de Persistencia](./03_plan_ejecucion/02_fase_persistencia/resumen_fase.md)
* 🔹 [Tarea 2.1 — Definición de Esquemas ORM (`models.py`)](./03_plan_ejecucion/02_fase_persistencia/tarea_2_1_modelos_orm.md)
* 🔹 [Tarea 2.2 — Conexión y Sesión Asíncrona (`connection.py`)](./03_plan_ejecucion/02_fase_persistencia/tarea_2_2_conexion_async.md)
* 🔹 [Tarea 2.3 — Implementación de Operaciones CRUD (`crud.py`)](./03_plan_ejecucion/02_fase_persistencia/tarea_2_3_operaciones_crud.md)
* 🔹 [Tarea 2.4 — Script de Inicialización y Sembrado (`seed.py`)](./03_plan_ejecucion/02_fase_persistencia/tarea_2_4_script_seed.md)

#### 📍 [Fase 3: Integraciones Externas y Herramientas del Agente (Tools)](./03_plan_ejecucion/03_fase_integraciones/resumen_fase.md)
* 🔹 [Tarea 3.1 — Autenticación y Cliente de Google Calendar (`calendar_tools.py`)](./03_plan_ejecucion/03_fase_integraciones/tarea_3_1_auth_google.md)
* 🔹 [Tarea 3.2 — Métodos Operativos de Calendar (`get_day_events`, `create_calendar_event`)](./03_plan_ejecucion/03_fase_integraciones/tarea_3_2_metodos_calendar.md)
* 🔹 [Tarea 3.3 — Envoltorios de Herramientas para el LLM (`registry.py`)](./03_plan_ejecucion/03_fase_integraciones/tarea_3_3_registry_tools.md)

#### 📍 [Fase 4: Orquestación del LLM y Conexión con Telegram](./03_plan_ejecucion/04_fase_orquestacion_llm/resumen_fase.md)
* 🔹 [Tarea 4.1 — Middleware de Autorización y Seguridad (`handlers.py`)](./03_plan_ejecucion/04_fase_orquestacion_llm/tarea_4_1_middleware_seguridad.md)
* 🔹 [Tarea 4.2 — Configuración del Motor del Agente (`engine.py`)](./03_plan_ejecucion/04_fase_orquestacion_llm/tarea_4_2_motor_agente.md)
* 🔹 [Tarea 4.3 — Diseño del System Prompt (`prompts.py`)](./03_plan_ejecucion/04_fase_orquestacion_llm/tarea_4_3_system_prompt.md)
* 🔹 [Tarea 4.4 — Enrutamiento de Mensajes y Comandos Rápidos](./03_plan_ejecucion/04_fase_orquestacion_llm/tarea_4_4_handlers_comandos.md)

#### 📍 [Fase 5: Programación Proactiva y Mensajería Automática](./03_plan_ejecucion/05_fase_programacion_proactiva/resumen_fase.md)
* 🔹 [Tarea 5.1 — Integración de APScheduler en el Ciclo de Eventos](./03_plan_ejecucion/05_fase_programacion_proactiva/tarea_5_1_apscheduler.md)
* 🔹 [Tarea 5.2 — Implementación del Briefing Matutino (Cron: 08:00 AM)](./03_plan_ejecucion/05_fase_programacion_proactiva/tarea_5_2_briefing_matutino.md)
* 🔹 [Tarea 5.3 — Implementación del Check-in Nocturno (Cron: 21:30 PM)](./03_plan_ejecucion/05_fase_programacion_proactiva/tarea_5_3_checkin_nocturno.md)
* 🔹 [Tarea 5.4 — Manejador de Respuestas de Teclado (`CallbackQueryHandler`)](./03_plan_ejecucion/05_fase_programacion_proactiva/tarea_5_4_callback_keyboards.md)

#### 📍 [Fase 6: Empaquetado, Despliegue y Monitorización](./03_plan_ejecucion/06_fase_despliegue_monitorizacion/resumen_fase.md)
* 🔹 [Tarea 6.1 — Construcción del Dockerfile de Producción](./03_plan_ejecucion/06_fase_despliegue_monitorizacion/tarea_6_1_dockerfile.md)
* 🔹 [Tarea 6.2 — Orquestación Completa en Compose (`docker-compose.yml`)](./03_plan_ejecucion/06_fase_despliegue_monitorizacion/tarea_6_2_compose_produccion.md)
* 🔹 [Tarea 6.3 — Despliegue en Servidor (VPS / Raspberry Pi)](./03_plan_ejecucion/06_fase_despliegue_monitorizacion/tarea_6_3_despliegue_vps.md)
* 🔹 [Tarea 6.4 — Sistema de Logs y Alertas de Fallos en Telegram](./03_plan_ejecucion/06_fase_despliegue_monitorizacion/tarea_6_4_logging_alertas.md)

---

## 🛠️ Stack Tecnológico Utilizado

* **Lenguaje & Core:** Python 3.11+, `asyncio`
* **Bot & UI:** `python-telegram-bot` v21+
* **LLM Core:** OpenAI / Gemini / Anthropic API con Function Calling
* **Persistencia:** PostgreSQL 16, `SQLAlchemy (Async)`, `asyncpg`
* **Integración API:** Google Calendar API (`google-api-python-client`)
* **Scheduler:** `APScheduler` (`AsyncIOScheduler`)
* **Esquemas:** `Pydantic` v2, `pydantic-settings`
* **Despliegue:** Docker, Docker Compose
