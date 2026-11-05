# djangomarketplace

## Ejecutar en local

```bash
python -m venv env
source env/bin/activate
pip install -r ../requirements.txt
cp ../.env.example ../.env   # y rellena SECRET_KEY
cd magicbeautybox
python manage.py migrate
python manage.py runserver
```

Abre http://127.0.0.1:8000/

## Ejecutar con Docker

Desde la raíz del repositorio:

```bash
cp .env.example .env   # y rellena SECRET_KEY
docker compose up --build
```

Servicios: `web` (Gunicorn, interno) y `nginx` (puerto 8000 del host). Con `DEBUG=False` la app exige HTTPS (`SECURE_SSL_REDIRECT`), así que para probar en local usa `DEBUG=True` o pon un proxy TLS delante.

## Imágenes subidas (media/)

Las imágenes de los artículos se guardan en `magicbeautybox/media/`. Cómo se sirven depende del modo:

- **Desarrollo (`DEBUG=True`):** Django sirve `/media/` directamente con `static()` (ver `magicbeautybox/urls.py`).
- **Producción / Docker (`DEBUG=False`):** Django ya no sirve `/media/`. Lo hace **nginx** (`nginx/default.conf`), que lee el volumen `media_data`. Ese mismo volumen está montado en `web` (donde Django escribe las imágenes) y en `nginx` (solo lectura, en `/var/www/media`). Así, lo que sube Django aparece inmediatamente en nginx sin copiar archivos.

Con Docker, nginx es el único servicio publicado: entra por `http://localhost:8000` y reenvía el resto a Gunicorn. Los uploads se limitan a 5 MB (`client_max_body_size 6m` en nginx y validación en el formulario).

Si respaldas el sitio, respalda el volumen `media_data` junto con la base de datos.

## Tests

```bash
cd magicbeautybox
python manage.py test
```
