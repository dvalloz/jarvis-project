# 📍 Fase 6: Empaquetado, Despliegue y Monitorización (Resumen de Fase)

En esta fase final se construye el `Dockerfile` de producción, se orquestan los servicios en Compose, se realiza el despliegue en servidor VPS y se configura la monitorización y notificaciones de error.

---

## 📂 Documentos de Tarea Incluidos

1. 🔹 [Tarea 6.1 — Construcción del Dockerfile de Producción](./tarea_6_1_dockerfile.md)
2. 🔹 [Tarea 6.2 — Orquestación Completa en Compose (`docker-compose.yml`)](./tarea_6_2_compose_produccion.md)
3. 🔹 [Tarea 6.3 — Despliegue en Servidor (VPS / Raspberry Pi)](./tarea_6_3_despliegue_vps.md)
4. 🔹 [Tarea 6.4 — Sistema de Logs y Alertas de Fallos en Telegram](./tarea_6_4_logging_alertas.md)

---

## 🎯 Entregables Globales de la Fase

* Imagen Docker liviana multi-etapa para la aplicación Python.
* Orquestación de producción en `docker-compose.yml` conectando bot y base de datos.
* Despliegue 24/7 en VPS con políticas de reinicio automático (`unless-stopped`).
* Capturador de excepciones que notifica el traceback del error por Telegram al usuario.
