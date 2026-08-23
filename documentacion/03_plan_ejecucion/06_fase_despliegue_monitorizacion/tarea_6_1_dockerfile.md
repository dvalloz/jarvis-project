# 🔹 Tarea 6.1 — Construcción del Dockerfile de Producción

## 🎯 Objetivo
Construir una imagen Docker optimizada, multi-etapa y segura basada en `python:3.11-slim` para ejecutar la aplicación en producción.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `Dockerfile` en la raíz del proyecto:**
   ```dockerfile
   # Stage 1: Build dependencies
   FROM python:3.11-slim as builder

   WORKDIR /app
   RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

   COPY requirements.txt .
   RUN pip install --no-cache-dir --user -r requirements.txt

   # Stage 2: Final runtime image
   FROM python:3.11-slim

   WORKDIR /app
   RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

   COPY --from=builder /root/.local /root/.local
   ENV PATH=/root/.local/bin:$PATH

   COPY . .

   # User non-root for security
   RUN useradd -m appuser && chown -R appuser:appuser /app
   USER appuser

   CMD ["python", "main.py"]
   ```

---

## ✅ Verificación de la Tarea
- Construir la imagen localmente:
  ```bash
  docker build -t jarvis-bot:latest .
  ```
- Comprobar que la imagen se construya sin errores y ocupe menos de 300MB.
