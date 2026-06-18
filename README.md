# Churn prediction MLOps

Projet de prédiction de churn client.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Sous Windows :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Exécution du pipeline

```bash
python main.py
```

Le pipeline entraîne un modèle et écrit les artefacts dans `artifacts/`.

## API

```bash
uvicorn app:app --reload --port 8000
```
Routes disponibles :

- `/health` (Statut de l'API)
- `/predict` (Nécessite le header `X-API-Key`)
- `/metrics` (Nécessite le header `X-API-Key`)

Pour faire une prédiction :
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "X-API-Key: churn-demo-token" \
     -H "Content-Type: application/json" \
     -d '{"tenure_months": 12, "monthly_charges": 75.5, "total_charges": 906.0, "contract": "Month-to-month"}'
```

## Tests

```bash
pytest
```
