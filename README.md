# StockSense AI — Stock Price Predictor

StockSense AI is a full-stack, AI-powered stock analytics web app where users can:

- Search Indian and US stocks
- View historical OHLCV charts
- Get 7-day AI predictions with confidence and uncertainty bounds
- Receive Buy/Hold/Sell signals from model + technical indicators

> **Disclaimer:** This is **not financial advice**. Use predictions for educational/research purposes only.

---

## Screenshots

Add screenshots after running locally:

- Home page (`frontend`) showing search + trending + market overview
- Stock detail page showing historical + prediction tabs
- Signal badge and confidence bar section

Suggested file names:

- `docs/screenshots/home.png`
- `docs/screenshots/stock-detail.png`
- `docs/screenshots/prediction-chart.png`

Then embed:

```md
![Home](docs/screenshots/home.png)
![Stock Detail](docs/screenshots/stock-detail.png)
![Prediction](docs/screenshots/prediction-chart.png)
```

---

## Project Structure

```text
stocksense-ai/
├── training/
│   ├── train.py
│   ├── dataset.py
│   ├── model.py
│   ├── export_onnx.py
│   ├── stock_list.py
│   ├── StockSense_Training.ipynb
│   └── requirements.txt
├── backend/
│   ├── main.py
│   ├── predictor.py
│   ├── stock_data.py
│   ├── signal_generator.py
│   ├── model/
│   │   ├── stocksense_model.onnx
│   │   └── scalers.json
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

---

## 1) Train overnight on Google Colab Pro (GPU)

Use `training/StockSense_Training.ipynb`.

What it does:

1. Checks GPU and VRAM
2. Installs dependencies
3. Mounts Google Drive
4. Copies training scripts
5. Downloads stock data via **yfinance** (free, no API key)
6. Trains LSTM-attention model for 100 epochs (or early stopping)
7. Plots loss/MAE curves
8. Exports ONNX
9. Saves model/scalers to Drive + optional direct download
10. Verifies CPU-only ONNX inference

### Colab tips

- Runtime: **GPU** (T4/V100/A100 depending plan)
- Keep browser tab active for long runs
- Save outputs periodically to Drive

---

## 2) Copy model artifacts to backend

After training, ensure these files exist in `backend/model/`:

- `stocksense_model.onnx`
- `scalers.json`

If using notebook outputs:

- Copy from `/content/training/` or Drive folder to local `backend/model/`.

---

## 3) Run locally

## Backend (FastAPI)

1. Create and activate virtual environment
2. Install dependencies from `backend/requirements.txt`
3. Start API server from `backend/`

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected API base URL: `http://localhost:8000`

Key endpoints:

- `GET /stock/{symbol}`
- `GET /stock/{symbol}/history`
- `GET /search?q={query}`
- `GET /trending`
- `GET /health`

## Frontend (React + Tailwind)

1. Install dependencies in `frontend/`
2. Start dev server
3. Open `http://localhost:5173`

```bash
cd frontend
npm install
npm run dev
```

The frontend calls backend at `http://localhost:8000` by default.
Set `VITE_API_BASE_URL` if needed.

---

## 4) Deploy (Vercel + Render)

## Frontend on Vercel

- Import `frontend/` as project root
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable:
  - `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`

## Backend on Render

- Create a new Web Service from `backend/`
- Runtime: Python
- Install command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port 10000`
- Add persistent model files in `backend/model/` (ONNX + scalers)

---

## 5) GPU usage explanation

- **Training:** Uses GPU in Colab for faster LSTM training.
- **Inference (production):** Uses **CPU only** via `onnxruntime`.
- No GPU, no paid API, and no external model serving required at runtime.

This architecture keeps cost low and deployment simple.

---

## 6) Tech stack

- Training: PyTorch, pandas, numpy, ta, yfinance, onnx
- Inference: ONNX Runtime (CPUExecutionProvider)
- Backend: FastAPI + cachetools + yfinance
- Frontend: React + Tailwind + Recharts + React Query

---

## 7) Important compliance note

StockSense AI is for educational and informational purposes only.
It does not provide investment advice, portfolio recommendations, or guarantees of returns.

**Not financial advice.**
# StockSense-Ai
