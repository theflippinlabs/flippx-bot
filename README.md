# Twitter Bot — Control Panel

Un bot Twitter avec panneau de contrôle React et backend FastAPI.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| Backend | FastAPI + Tweepy + APScheduler |
| DB | SQLite (dev) / PostgreSQL (prod) |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway |

## Features

- **Dashboard** — Envoyer des tweets manuellement, voir les logs
- **Scheduler** — Programmer des tweets à une date/heure précise
- **Queue** — File d'attente avec priorités, pause/reprise
- **Auto-reply** — Répondre automatiquement aux mentions par mot-clé
- **Analytics** — Likes, retweets, impressions, engagement rate

## Démarrage rapide

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis remplis tes clés Twitter
uvicorn app.main:app --reload
```

L'API sera disponible sur `http://localhost:8000`
Swagger UI : `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # puis pointe vers ton API
npm run dev
```

Le dashboard sera disponible sur `http://localhost:5173`

## Déploiement

### Backend → Railway

1. Crée un projet sur [railway.app](https://railway.app)
2. Connecte ce repo GitHub → sélectionne le dossier `backend`
3. Ajoute tes variables d'environnement dans Railway (copie depuis `.env.example`)
4. Railway détecte automatiquement `railway.toml`

### Frontend → Vercel

1. Importe ce repo sur [vercel.com](https://vercel.com)
2. Définis le **Root Directory** sur `frontend`
3. Ajoute les variables d'environnement :
   - `VITE_API_URL` → URL de ton service Railway
   - `VITE_API_KEY` → ta clé API dashboard

## Clés Twitter API v2

1. Crée un compte développeur sur [developer.twitter.com](https://developer.twitter.com)
2. Crée un projet et une app
3. Active les permissions **Read + Write**
4. Génère les tokens et remplis ton `.env`

## Structure

```
twitter-bot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── routes/
│   │   └── services/
│   ├── requirements.txt
│   └── railway.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/api.ts
│   ├── vercel.json
│   └── package.json
└── .github/workflows/
```
