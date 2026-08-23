# 📍 Fase 3: Integraciones Externas y Herramientas del Agente (Tools) (Resumen de Fase)

En esta fase se desarrolla la integración con Google Calendar API y se empaquetan las funciones del sistema (calendario, entrenamientos y tareas) dentro de firmas de herramientas estandarizadas (*Tool Calling*) registradas en `tools/registry.py`.

---

## 📂 Documentos de Tarea Incluidos

1. 🔹 [Tarea 3.1 — Autenticación y Cliente de Google Calendar (`calendar_tools.py`)](./tarea_3_1_auth_google.md)
2. 🔹 [Tarea 3.2 — Métodos Operativos de Calendar (`get_day_events`, `create_calendar_event`)](./tarea_3_2_metodos_calendar.md)
3. 🔹 [Tarea 3.3 — Envoltorios de Herramientas para el LLM (`registry.py`)](./tarea_3_3_registry_tools.md)

---

## 🎯 Entregables Globales de la Fase

* Flujo de autorización OAuth2 capaz de guardar y refrescar `credentials/google_token.json`.
* Funciones operativas para consultar citas por fecha e insertar nuevos eventos en la agenda.
* Módulo `tools/registry.py` con las especificaciones JSON Schema que consume el motor LLM.
