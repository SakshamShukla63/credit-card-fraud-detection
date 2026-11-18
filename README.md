# Radar - Credit Card Fraud Detection

Radar is a full-stack credit-card fraud detection demo. It trains an XGBoost classifier, exposes predictions through FastAPI, and provides a React dashboard for transaction analysis.

## Features

- XGBoost fraud probability model
- FastAPI prediction, metadata, sample, and health endpoints
- React and Tailwind transaction dashboard
- Random transaction samples from the training dataset
- Plain-English risk explanations
- Configured Vite API proxy

## Project structure

```text
fraud-detection/
  backend/
    app/
      main.py
      narrative.py
    data/
      creditcard.csv
    models/
      model.pkl
      scaler.pkl
      feature_names.json
      metadata.json
    train.py
    requirements.txt
  frontend/
    src/
      main.jsx
      index.css
    index.html
    package.json
    vite.config.js
```

## Dataset setup

Download the Kaggle Credit Card Fraud Detection dataset and save it as:

```text
backend/data/creditcard.csv
```

The repository ignores this CSV because it is approximately 144 MB and too large for convenient GitHub hosting. The Kaggle dataset can be downloaded from:

https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

## Backend setup

Windows PowerShell:

```powershell
cd fraud-detection

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Train the model:

```powershell
python backend\train.py
```

Start the API:

```powershell
python -m uvicorn app.main:app `
  --app-dir backend `
  --host 127.0.0.1 `
  --port 8000 `
  --reload
```

The API is available at `http://127.0.0.1:8000`, and interactive documentation is available at `http://127.0.0.1:8000/docs`.

## Frontend setup

Open a second terminal:

```powershell
cd fraud-detection\frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`.

## API endpoints

- `GET /api/health` - API and model readiness
- `GET /api/metadata` - dataset and model metrics
- `GET /api/sample` - random dataset transaction
- `POST /api/predict` - predict a transaction

## Example prediction request

```json
{
  "Time": 86400,
  "Amount": 249.5,
  "features": {}
}
```

## Production frontend build

```powershell
cd frontend
npm run build
```

The build output is written to `frontend/dist`.

