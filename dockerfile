FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instala dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el proyecto
COPY . .

# Expone el puerto
EXPOSE 8000

# Aplica migraciones, recopila estáticos e inicia Gunicorn
WORKDIR /app/djangomarketplace/magicbeautybox
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn magicbeautybox.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
