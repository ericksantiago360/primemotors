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

## Tests

```bash
cd magicbeautybox
python manage.py test
```
