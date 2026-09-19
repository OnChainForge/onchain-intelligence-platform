from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class WalletCreate(BaseModel):
    address: str
    label: Optional[str] = None


class WalletOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    address: str
    label: Optional[str]
    is_active: bool
    current_score: float
    last_scored_at: Optional[datetime]
    added_at: datetime


class ScoreSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wallet_id: int
    score: float
    tx_count: int
    total_value_eth: float
    contract_interactions: int
    reasoning: Optional[str]
    created_at: datetime


class WalletAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wallet_id: int
    message: str
    score_at_alert: float
    created_at: datetime
    resolved: bool
