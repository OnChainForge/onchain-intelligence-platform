import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.logging_config import setup_logging
from app.scheduler import run_scoring_loop
from app.routers import wallets, alerts

setup_logging()
logger = logging.getLogger("main")

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starts the background wallet-scoring loop when the app boots."""
    scoring_task = asyncio.create_task(run_scoring_loop())
    logger.info("Scoring task started in background.")
    yield
    scoring_task.cancel()
    logger.info("Scoring task cancelled.")


app = FastAPI(
    title="On-Chain Intelligence Platform",
    description="Tracks Ethereum wallets, computes explainable risk scores from on-chain activity, and raises alerts when scores cross a threshold.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallets.router)
app.include_router(alerts.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
