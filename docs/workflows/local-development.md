# Local Development Setup

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs

## Backend Only

```bash
cd apps/api
pip install -r requirements.txt
uvicorn apps.api.app.main:app --reload
```

Set `DATABASE_URL=sqlite:///./civic_pulse.db` for a lightweight local backend without Postgres.

## Frontend Only

```bash
cd apps/web
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` when the API runs separately.

## Testing

```bash
pytest
```
