# CosmoCore Enterprise Platform

Dual-engine astrology API (Western tropical + Vedic sidereal) powered by **Swiss Ephemeris** (`pyswisseph`), with PostgreSQL persistence, Redis/Celery background transit caching, and an Expo mobile client.

## Stack

| Layer | Technology |
|-------|------------|
| Ephemeris | pyswisseph 2.10 |
| API | FastAPI + Uvicorn |
| DB | PostgreSQL |
| Queue | Celery + Redis |
| Mobile | React Native (Expo) |

## Quick start (Docker)

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USER/cosmocore.git
cd cosmocore

# 2. Download ephemeris files into backend/ephe (see backend/ephe/README.md)

# 3. Start services
docker compose up --build

# 4. API docs
open http://localhost:8000/docs
```

## Local development

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# PostgreSQL + Redis running; apply schema:
psql "$DATABASE_URL" -f schema.sql

uvicorn app:app --reload
```

### Celery

```bash
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

## API

`POST /api/v1/chart/compute` — compute and optionally persist full chart.

```json
{
  "display_name": "Alex",
  "birth_date": "1995-08-15",
  "birth_time": "14:30",
  "latitude": 40.7128,
  "longitude": -74.006,
  "timezone_id": "America/New_York",
  "current_age": 28.5,
  "persist": true
}
```

Other routes:

- `GET /health`
- `GET /api/v1/profile/{user_id}`
- `GET /api/v1/transits/global/latest`

## Mobile

```bash
cd mobile
npm install
# Point to your machine IP if on a physical device:
# set EXPO_PUBLIC_API_URL=http://192.168.1.x:8000
npm start
```

## Push to GitHub

See [GITHUB_SETUP.md](./GITHUB_SETUP.md).

## License

MIT
