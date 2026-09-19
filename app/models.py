from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Wallet(Base):
    """An Ethereum address being tracked for on-chain activity and risk scoring."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(80), unique=True, nullable=False, index=True)
    label = Column(String(120), nullable=True)  # optional human-readable name
    is_active = Column(Boolean, default=True)
    current_score = Column(Float, default=0.0)
    last_scored_at = Column(DateTime, nullable=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    score_history = relationship("ScoreSnapshot", back_populates="wallet", cascade="all, delete-orphan")
    alerts = relationship("WalletAlert", back_populates="wallet", cascade="all, delete-orphan")


class ScoreSnapshot(Base):
    """A point-in-time risk score for a wallet, so score changes can be tracked over time."""
    __tablename__ = "score_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    score = Column(Float, nullable=False)
    tx_count = Column(Integer, nullable=False)
    total_value_eth = Column(Float, nullable=False)
    contract_interactions = Column(Integer, nullable=False)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    wallet = relationship("Wallet", back_populates="score_history")


class WalletAlert(Base):
    """Generated when a wallet's score crosses a significant threshold."""
    __tablename__ = "wallet_alerts"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    message = Column(Text, nullable=False)
    score_at_alert = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved = Column(Boolean, default=False)

    wallet = relationship("Wallet", back_populates="alerts")
