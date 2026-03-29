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

# Comando para iniciar el servidor
CMD ["python", "djangomarketplace/magicbeautybox/manage.py", "runserver", "0.0.0.0:8000"]