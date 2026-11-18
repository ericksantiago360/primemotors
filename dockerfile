FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Usuario sin privilegios para ejecutar la aplicación
RUN groupadd --system app && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app

# Instala dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el proyecto
COPY . .

# Estáticos recopilados en build (como root), para no necesitar escritura en tiempo de ejecución.
# SECRET_KEY es solo para que settings.py cargue; no se usa para nada aquí.
# Carpetas de datos: la base (db.sqlite3) y media/ se montan como volúmenes con nombre.
RUN SECRET_KEY=build-only python djangomarketplace/magicbeautybox/manage.py collectstatic --noinput \
    && mkdir -p /app/data /app/djangomarketplace/magicbeautybox/media \
    && chown -R app:app /app/data /app/djangomarketplace/magicbeautybox/media

ENV SQLITE_PATH=/app/data/db.sqlite3

# Expone el puerto
EXPOSE 8000

USER app

# Aplica migraciones e inicia Gunicorn
WORKDIR /app/djangomarketplace/magicbeautybox
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn magicbeautybox.wsgi:application --bind 0.0.0.0:8000 --workers 3 --no-control-socket"]
