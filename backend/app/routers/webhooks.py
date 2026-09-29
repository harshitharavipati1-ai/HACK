import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident
from app.schemas import ApiResponse, WebhookAlertPayload, IncidentResponse
from app.services.redaction_service import redact_secrets

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/alert", response_model=ApiResponse)
def alertmanager_webhook(payload: WebhookAlertPayload, db: Session = Depends(get_db)):
    title = payload.title or payload.alert or payload.summary or f"Alert for {payload.service_name}"
    alert_raw = payload.alert or payload.summary or title
    logs_raw = payload.logs or (json.dumps(payload.annotations) if payload.annotations else "No detailed log payload attached.")
    
    # Redact secrets BEFORE storing
    safe_alert = redact_secrets(alert_raw)
    safe_logs = redact_secrets(logs_raw)
    
    count = db.query(Incident).count() + 1
    inc_id = f"INC-2026-{count:03d}"
    
    inc = Incident(
        id=inc_id,
        title=title,
        service_name=payload.service_name,
        environment=payload.environment,
        severity=payload.severity.upper(),
        status="OPEN",
        alert=safe_alert,
        logs=safe_logs,
        created_by="pagerduty-webhook",
        tags=json.dumps([payload.service_name, payload.severity.lower(), "webhook"])
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    
    res = IncidentResponse.model_validate(inc)
    res.tags = [payload.service_name, payload.severity.lower(), "webhook"]
    return ApiResponse(success=True, data=res.model_dump())
