FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema si son necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Exponer el puerto interno
EXPOSE 8000

# Ejecutar con Gunicorn (Asegúrate de cambiar 'monagua' si tu carpeta wsgi se llama diferente)
CMD ["gunicorn", "monagua.wsgi:application", "--bind", "0.0.0.0:8000"]