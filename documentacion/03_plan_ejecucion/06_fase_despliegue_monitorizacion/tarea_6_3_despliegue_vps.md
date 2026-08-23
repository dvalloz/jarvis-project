# 🔹 Tarea 6.3 — Despliegue en Servidor (VPS / Raspberry Pi)

## 🎯 Objetivo
Desplegar la aplicación en un servidor en la nube (VPS en Hetzner/DigitalOcean) o servidor local (Raspberry Pi/Home Server) funcionando 24/7.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Preparar el Servidor Destino:**
   * Conéctate por SSH al servidor: `ssh usuario@tu-ip-servidor`.
   * Instala Git, Docker y Docker Compose si no están instalados.

2. **Clonar el Repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/telegram-ai-assistant.git
   cd telegram-ai-assistant
   ```

3. **Configurar Entorno y Credenciales:**
   * Crea el archivo `.env` en el servidor con los valores de producción.
   * Sube o genera el archivo `credentials/google_credentials.json`.
   * Realiza la primera autenticación OAuth2 para generar `credentials/google_token.json`.

4. **Desplegar Servicios:**
   ```bash
   docker compose up -d --build
   ```

---

## ✅ Verificación de la Tarea
- Verificar el estado de los contenedores:
  ```bash
  docker compose ps
  ```
- Probar enviar un mensaje `/hoy` al bot de Telegram y comprobar la respuesta del servidor en tiempo real.
