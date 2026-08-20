# catalogo-app

Catálogo independiente en Django para un solo negocio, con catálogo público, panel privado y admin nativo de respaldo.

## Requisitos previos

- Python 3.10 o superior.
- SQLite para desarrollo local.
- `pip` y `venv`.

## Instalación

```bash
cd /var/www/sisbar/catalogo-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Variables de entorno

Edita `.env` y ajusta:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`

Opcionalmente, deja `DJANGO_DEBUG=1` para desarrollo local.

## Base de datos

Este proyecto usa SQLite por defecto. La base se crea automáticamente en:

```text
catalogo-app/db.sqlite3
```

Luego ejecuta:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Superusuario de ejemplo

Para crear un usuario administrador de prueba:

```bash
python manage.py createsuperuser
```

Si quieres crear uno con datos de ejemplo manualmente, usa credenciales válidas y marca el usuario como `staff`.

## Arranque local

```bash
python manage.py runserver 127.0.0.1:8001
```

## Rutas principales

- Catálogo público: `/`
- Panel propio: `/panel/`
- Login del panel: `/panel/login/`
- Django admin nativo: `/admin/`

## Despliegue en Render

El proyecto incluye `render.yaml` y `build.sh` para desplegar un servicio Django con Gunicorn y PostgreSQL.

1. Sube el contenido de esta carpeta a un repositorio de GitHub, sin incluir `.env`, `db.sqlite3`, `media/` ni `.venv/`.
2. En Render, crea un servicio desde el Blueprint del repositorio o conecta el repositorio manualmente.
3. Configura `ADMIN_EMAIL` y `ADMIN_PASSWORD` en las variables del servicio. El comando de construcción crea o actualiza el superusuario de forma segura.
4. Render crea PostgreSQL desde el Blueprint y entrega `DATABASE_URL` al servicio. Para un servicio creado manualmente, conecta una base PostgreSQL y copia su URL interna en `DATABASE_URL`.
5. Usa `bash build.sh` como Build Command y `gunicorn catalogo_app.wsgi:application --bind 0.0.0.0:$PORT` como Start Command.

Render tiene disco efímero por defecto. El Blueprint incluye un disco persistente en `/var/data`, usado para `MEDIA_ROOT`; consérvalo si vas a subir logos, fotos o videos. Para escalar a varias instancias, mueve media a almacenamiento de objetos antes de hacerlo.
