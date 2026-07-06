# Bot de moderación (Fase 1: esqueleto)

## Setup local
1. `pip install -r requirements.txt`
2. Copia `.env.example` a `.env` y rellena `DISCORD_TOKEN` y `DATABASE_URL`
3. `python main.py`
4. En Discord: `/ping` debe responder con la latencia y el estado de la base de datos

## Desplegar en Railway
1. Sube esta carpeta a un repo de GitHub
2. En Railway: New Project → Deploy from GitHub repo → selecciona el repo
3. Añade el plugin **PostgreSQL** desde Railway (esto crea `DATABASE_URL` automáticamente)
4. En Variables del servicio del bot, añade `DISCORD_TOKEN` con el token del bot
5. Railway hace deploy automático usando el `Procfile`

## Estructura
- `main.py` — arranque del bot, carga de cogs
- `core/config.py` — variables de entorno
- `core/database.py` — pool de conexión a Postgres
- `cogs/` — cada módulo de funcionalidad (welcome, antinuke, moderación, tickets, etc. se irán añadiendo aquí)
