# 🔹 Tarea 1.2 — Configuración de Google Cloud y OAuth2

## 🎯 Objetivo
Configurar una aplicación en Google Cloud Console, habilitar la **Google Calendar API** y generar las credenciales OAuth2 necesarias para sincronizar eventos y citas.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear Proyecto en Google Cloud:**
   * Accede a [Google Cloud Console](https://console.cloud.google.com/).
   * Haz clic en el selector de proyectos y pulsa en **Nuevo Proyecto**.
   * Nómbralo `telegram-personal-assistant` y pulsa **Crear**.

2. **Habilitar Google Calendar API:**
   * En el menú lateral, dirígete a **APIs y servicios > Biblioteca**.
   * Busca `Google Calendar API`.
   * Pulsa en el resultado y haz clic en **Habilitar**.

3. **Configurar Pantalla de Consentimiento OAuth:**
   * Navega a **APIs y servicios > Pantalla de consentimiento de OAuth**.
   * Selecciona el tipo de usuario **External** (Externo) y haz clic en **Crear**.
   * Rellena el nombre de la app (`Jarvis Calendar Bot`) y tu correo de contacto.
   * En la sección de **Usuarios de prueba (Test Users)**, añade la dirección de correo Gmail con la que gestionarás tu calendario.
   * Guarda y continúa.

4. **Generar y Descargar Credenciales:**
   * Dirígete a **APIs y servicios > Credenciales**.
   * Haz clic en **Crear credenciales > ID de cliente de OAuth**.
   * En *Tipo de aplicación*, selecciona **Aplicación para ordenador (Desktop Application)**.
   * Nombra la credencial (ej. `Jarvis Desktop Client`) y pulsa **Crear**.
   * Descarga el archivo JSON generado.
   * Renombra el archivo como `google_credentials.json` y colócalo en la carpeta `credentials/` en la raíz de tu proyecto.

---

## ✅ Verificación de la Tarea
- Verificar que el archivo exista en `credentials/google_credentials.json`.
- Confirmar que contenga las claves `"installed"` con `"client_id"` y `"client_secret"`.
