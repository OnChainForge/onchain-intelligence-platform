from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[schemas.WalletAlertOut])
def list_alerts(
    resolved: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(models.WalletAlert)
    if resolved is not None:
        query = query.filter(models.WalletAlert.resolved == resolved)
    return query.order_by(models.WalletAlert.created_at.desc()).limit(50).all()


@router.patch("/{alert_id}/resolve", response_model=schemas.WalletAlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(models.WalletAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    db.commit()
    db.refresh(alert)
    return alert
