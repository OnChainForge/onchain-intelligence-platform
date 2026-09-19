from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from web3 import Web3

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", response_model=schemas.WalletOut)
def add_wallet(wallet: schemas.WalletCreate, db: Session = Depends(get_db)):
    """Registers a new wallet address to track and score."""
    if not Web3.is_address(wallet.address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")

    checksum_address = Web3.to_checksum_address(wallet.address)
    existing = db.query(models.Wallet).filter(models.Wallet.address == checksum_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="This wallet is already being tracked")

    db_wallet = models.Wallet(address=checksum_address, label=wallet.label)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet


@router.get("/", response_model=list[schemas.WalletOut])
def list_wallets(db: Session = Depends(get_db)):
    """Lists tracked wallets, highest risk score first."""
    return db.query(models.Wallet).order_by(models.Wallet.current_score.desc()).all()


@router.get("/{wallet_id}/history", response_model=list[schemas.ScoreSnapshotOut])
def wallet_score_history(wallet_id: int, db: Session = Depends(get_db)):
    """Returns the full score history for a wallet, most recent first."""
    wallet = db.get(models.Wallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return (
        db.query(models.ScoreSnapshot)
        .filter(models.ScoreSnapshot.wallet_id == wallet_id)
        .order_by(models.ScoreSnapshot.created_at.desc())
        .all()
    )


@router.delete("/{wallet_id}")
def remove_wallet(wallet_id: int, db: Session = Depends(get_db)):
    """Stops tracking a wallet and deletes its history."""
    wallet = db.get(models.Wallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    db.delete(wallet)
    db.commit()
    return {"detail": "Wallet removed"}
