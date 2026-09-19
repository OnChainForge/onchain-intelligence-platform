import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.blockchain import get_latest_block_number, get_wallet_activity
from app.scoring import calculate_score
from app.models import Wallet, ScoreSnapshot, WalletAlert

logger = logging.getLogger("scheduler")

ALERT_SCORE_THRESHOLD = 60.0


def score_wallet(wallet_id: int) -> None:
    """
    Recomputes a single wallet's score from recent on-chain activity,
    stores a snapshot, updates the wallet's current score, and raises
    a WalletAlert if the score crosses the alert threshold.
    Runs in a worker thread since it performs blocking RPC calls.
    """
    db = SessionLocal()
    try:
        wallet = db.get(Wallet, wallet_id)
        if wallet is None or not wallet.is_active:
            return

        latest_block = get_latest_block_number()
        from_block = max(0, latest_block - settings.lookback_blocks)

        activity = get_wallet_activity(wallet.address, from_block, latest_block)
        score, reasoning = calculate_score(activity)

        snapshot = ScoreSnapshot(
            wallet_id=wallet.id,
            score=score,
            tx_count=activity["tx_count"],
            total_value_eth=activity["total_value_eth"],
            contract_interactions=activity["contract_interactions"],
            reasoning=reasoning,
        )
        db.add(snapshot)

        previous_score = wallet.current_score
        wallet.current_score = score
        wallet.last_scored_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Scored wallet {wallet.address}: {score:.1f} ({reasoning})")

        if score >= ALERT_SCORE_THRESHOLD and previous_score < ALERT_SCORE_THRESHOLD:
            alert = WalletAlert(
                wallet_id=wallet.id,
                message=f"Wallet {wallet.address} risk score crossed {ALERT_SCORE_THRESHOLD}: {reasoning}",
                score_at_alert=score,
            )
            db.add(alert)
            db.commit()
            logger.info(f"ALERT: wallet {wallet.address} crossed risk threshold ({score:.1f})")

    except Exception as e:
        logger.error(f"Error scoring wallet {wallet_id}: {e}")
        db.rollback()
    finally:
        db.close()


async def run_scoring_loop():
    """Periodically re-scores every active wallet being tracked."""
    logger.info("Starting wallet scoring loop...")

    while True:
        try:
            db = SessionLocal()
            try:
                wallet_ids = [w.id for w in db.query(Wallet).filter(Wallet.is_active.is_(True)).all()]
            finally:
                db.close()

            for wallet_id in wallet_ids:
                await asyncio.to_thread(score_wallet, wallet_id)

        except Exception as e:
            logger.error(f"Error in scoring loop: {e}")

        await asyncio.sleep(settings.poll_interval_seconds)
