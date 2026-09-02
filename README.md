# SlopeSense NER

Landslide early-warning demo for India's North Eastern Region (Smart India Hackathon). Web PWA + FastAPI risk engine + GIS layers.

## Quick start (no Docker)

```powershell
cd "d:\SIH PROJECT"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r apps/api/requirements.txt
python ml/generate_gis.py
python ml/train.py
cd apps/api
$env:PYTHONPATH = "d:\SIH PROJECT"
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd "d:\SIH PROJECT\apps\web"
npm install
npm run dev
```

Open http://localhost:3000

Demo logins (password `demo123`): `citizen`, `field`, `district`, `sdma`

## Docker

```powershell
python ml/generate_gis.py
python ml/train.py
docker compose up --build
```

## Honesty for judges

Live rainfall uses Open-Meteo. IMD satellite, soil sensors, and SMS delivery are adapter interfaces with mock/stub implementations matching production contracts.
