# On-Chain Intelligence Platform

Wallet risk scoring platform: register Ethereum addresses to monitor, get an explainable 0-100 risk score based on recent on-chain activity, and receive alerts when a wallet crosses a risk threshold.

## Problem

Assessing whether a wallet is "risky" (bot activity, contract-interaction farming, unusual volume spikes) typically requires either expensive third-party intelligence APIs or manual on-chain digging. There's no lightweight, transparent way to continuously track a watchlist of wallets and get an explainable score.

## Solution

Users register wallets to monitor. A background scheduler periodically pulls each wallet's recent activity (transaction frequency, volume, % of interactions with contracts) and computes a risk score using a transparent, rule-based heuristic — no black-box ML. When a wallet's score crosses a configurable threshold (60), an alert is generated.

## Architecture

┌────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Frontend │ │ FastAPI REST │ │ SQLite (WAL) │
│ Add wallet form │─────▶│ /wallets │─────▶│ wallets table │
│ (live validation)│ │ /alerts │ │ scores table │
└────────────────┘ └──────────────────┘ └────────┬────────┘
│
┌──────────────────┐ │
│ scheduler.py │ │
│ periodic background│◀──────────────┘
│ scoring loop │
└────────┬─────────────┘
│
▼
┌──────────────────┐ ┌─────────────────┐
│ blockchain.py │ │ scoring.py │
│ get_wallet_activity│─────▶│ calculate_score │
│ (via Infura RPC) │ │ (heuristic, 0-100) │
└──────────────────┘ └────────┬────────┘
│ score ≥ 60?
▼
┌─────────────────┐
│ Alert created │
└─────────────────┘


## Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite (WAL mode)
- **Blockchain:** Web3.py via Infura RPC
- **Scoring:** custom rule-based heuristic (`scoring.py`), no ML
- **Scheduling:** background periodic task (`scheduler.py`)
- **Frontend:** Vanilla HTML/CSS/JS, dark theme, polling-based
- **Config:** pydantic-settings (`.env`)

## Running locally

Backend:
```bash
cd onchain-intelligence-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your Infura API key
uvicorn app.main:app --reload --port 8003
```

Frontend:
```bash
cd frontend
python3 -m http.server 5503
```

## API

| Method | Endpoint              | Description                              |
|--------|------------------------|--------------------------------------------|
| GET    | `/wallets/`            | List monitored wallets                     |
| POST   | `/wallets/`             | Register a new wallet to monitor           |
| GET    | `/wallets/{address}`   | Get a wallet's details and score history   |
| GET    | `/alerts/`              | List generated risk alerts                 |
| GET    | `/health`               | Health check                               |

## Technical decisions

- **Rule-based scoring over ML:** heuristic scoring (weighted combination of tx frequency, volume, and contract-interaction ratio) keeps the score fully explainable — each component's contribution can be shown to the user, unlike a black-box model.
- **Periodic background scoring vs on-demand:** wallets are re-scored on a schedule so risk trends can be tracked over time (score history per wallet), rather than only reflecting a single snapshot.
- **Threshold as config:** the 60-point alert threshold lives in `.env` for easy tuning without redeploying.
- **SQLite over Postgres (local):** same constraint as the other projects — `psycopg2-binary` build issues on Python 3.14 locally. Postgres is planned for Render.

## Challenges & learnings

- Early version gave no visual confirmation when a wallet was successfully added — it looked like the request had silently failed even though it saved correctly. Fixed with a clear "✓ Wallet added successfully" message and a highlighted row for the newly added wallet.
- Balancing the scoring heuristic weights took iteration: an early version over-weighted raw transaction count, flagging normal high-frequency DeFi users as risky. Rebalanced to weight contract-interaction ratio and volume more heavily.

## License

MIT
