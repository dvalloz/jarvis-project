# 🔹 Tarea 1.1 — Creación y Securización del Bot de Telegram

## 🎯 Objetivo
Crear una nueva instancia de bot en Telegram a través de `@BotFather`, desactivar su capacidad de incorporarse a grupos para prevenir filtración de datos y obtener el `TELEGRAM_USER_ID` personal para restringir el acceso.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear el Bot con BotFather:**
   * Abre Telegram y busca la cuenta oficial `@BotFather`.
   * Envía el comando `/newbot`.
   * Introduce el nombre visible del bot (ej. `Jarvis Personal Assistant`).
   * Introduce el username del bot finalizado en `bot` (ej. `dvdva_jarvis_bot`).
   * Copia y guarda el token HTTP API generado (`TELEGRAM_BOT_TOKEN`).

2. **Securizar el Bot (Desactivar Grupos):**
   * En el chat con BotFather, envía `/setjoingroups`.
   * Selecciona el bot recién creado.
   * Selecciona **Disable** para evitar que cualquier usuario añada tu bot a un grupo público o de terceros.

3. **Obtener tu User ID de Telegram:**
   * Busca la cuenta oficial `@userinfobot` en Telegram.
   * Envía cualquier mensaje (ej. `/start`).
   * Copia tu ID numérico retornado (ej. `123456789`). Guarda este valor como `TELEGRAM_USER_ID`.

4. **Persistencia Inicial en `.env`:**
   * Crea un archivo `.env` en la raíz del proyecto con la siguiente estructura:
     ```env
     TELEGRAM_BOT_TOKEN="tu_token_aqui"
     TELEGRAM_USER_ID=123456789
     ```

---

## ✅ Verificación de la Tarea
- Verificar que el token funcione realizando una petición básica:
  * **Linux / Bash / Git Bash / Command Prompt:**
    ```bash
    curl -s https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getMe
    ```
  * **Windows PowerShell:**
    ```powershell
    curl.exe -s https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getMe
    # o bien:
    Invoke-RestMethod https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getMe
    ```
- Confirmar que el JSON devuelto responda `"ok": true`.
