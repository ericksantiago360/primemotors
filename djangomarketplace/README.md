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

Servicios: `web` (Gunicorn, interno) y `nginx` (puerto 8000 del host).

- **Desarrollo:** `docker compose up --build` carga también `docker-compose.override.yml`, que monta el código para ver los cambios sin reconstruir.
- **Producción:** `docker compose -f docker-compose.yml up -d --build` (sin el override). El código va dentro de la imagen.

Los datos viven en volúmenes con nombre: `db_data` (base SQLite, en `/app/data/db.sqlite3`) y `media_data` (imágenes). Borrar contenedores no los elimina; `docker compose down -v` sí. La imagen corre como usuario sin privilegios `app`.

Si ya tenías datos en `magicbeautybox/db.sqlite3`, cópialos al volumen una vez antes de usar el stack nuevo. Con `DEBUG=False` la app exige HTTPS (`SECURE_SSL_REDIRECT`), así que para probar en local usa `DEBUG=True` o pon un proxy TLS delante.

## Imágenes subidas (media/)

Las imágenes de los artículos se guardan en `magicbeautybox/media/`. Cómo se sirven depende del modo:

- **Desarrollo (`DEBUG=True`):** Django sirve `/media/` directamente con `static()` (ver `magicbeautybox/urls.py`).
- **Producción / Docker (`DEBUG=False`):** Django ya no sirve `/media/`. Lo hace **nginx** (`nginx/default.conf`), que lee el volumen `media_data`. Ese mismo volumen está montado en `web` (donde Django escribe las imágenes) y en `nginx` (solo lectura, en `/var/www/media`). Así, lo que sube Django aparece inmediatamente en nginx sin copiar archivos.

Con Docker, nginx es el único servicio publicado: entra por `http://localhost:8000` y reenvía el resto a Gunicorn. Los uploads se limitan a 5 MB (`client_max_body_size 6m` en nginx y validación en el formulario).

Si respaldas el sitio, respalda el volumen `media_data` junto con la base de datos.

## Chatbot (Claude)

El widget de chat (esquina inferior derecha) solo aparece para usuarios con sesión iniciada. Llama a `POST /chatbot/chat/`, que consulta la API de Claude con el inventario de vehículos disponibles. Sin sesión responde 401.

Configura en `.env`:

- `ANTHROPIC_API_KEY`: tu API key de Anthropic. Sin ella el chatbot responde con error 503.
- `CHATBOT_MODEL` (opcional): por defecto `claude-opus-5-5`.

Pruebas: `python manage.py test chatbot`

## Tests

```bash
cd magicbeautybox
python manage.py test
```
