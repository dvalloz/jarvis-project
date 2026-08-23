FROM python:3.12-slim

# Evitar búfer de salida y archivos .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Madrid

WORKDIR /app

# Instalar paquetes del sistema necesarios (tzdata para zona horaria)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY . .

# Comando por defecto para ejecutar Jarvis
CMD ["python", "main.py"]
