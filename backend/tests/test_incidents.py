import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
import app.database as app_db
from app.database import Base, get_db
from app.services.redaction_service import redact_secrets
from app.services.ranking_service import rank_recalled_evidence, extract_error_signatures
from app.services.confidence_service import compute_evidence_confidence
from app.services.llm_service import validate_historical_claims, parse_json_from_response

# Test database in-memory with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
app_db.engine = engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app_db.SessionLocal = TestingSessionLocal

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_secret_redaction():
    text = "Error in auth service with api_key=sk-live-1234567890abcdef1234567890 and email user@example.com and IP 192.168.1.1"
    redacted = redact_secrets(text)
    assert "[REDACTED]" in redacted or "[REDACTED_API_KEY]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_IP]" in redacted
    assert "sk-live-1234567890" not in redacted

def test_create_and_get_incident():
    res = client.post("/api/incidents", json={
        "title": "Payment API Connection Timeout",
        "service_name": "payment-api",
        "severity": "CRITICAL",
        "alert": "503 Service Unavailable",
        "logs": "sqlalchemy.exc.TimeoutError: QueuePool limit reached"
    })
    assert res.status_code == 200
    data = res.json()["data"]
    inc_id = data["id"]
    assert data["title"] == "Payment API Connection Timeout"
    
    # Get incident
    res_get = client.get(f"/api/incidents/{inc_id}")
    assert res_get.status_code == 200
    assert res_get.json()["data"]["id"] == inc_id

def test_seed_and_memory_stats():
    res_seed = client.post("/api/seed")
    assert res_seed.status_code == 200
    
    res_stats = client.get("/api/memory/stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()["data"]
    assert stats["total_resolved_incidents"] > 0
    assert "provider_name" in stats

def test_analyze_incident():
    client.post("/api/seed")
    res_list = client.get("/api/incidents")
    inc_id = res_list.json()["data"][0]["id"]
    
    res_analyze = client.post(f"/api/incidents/{inc_id}/analyze")
    assert res_analyze.status_code == 200
    data = res_analyze.json()["data"]
    assert "likely_root_cause" in data
    assert "confidence_score" in data
    assert "recalled_incidents" in data

def test_feedback_worked_and_did_not_work():
    res = client.post("/api/incidents", json={
        "title": "Auth Service Redis Memory Spike",
        "service_name": "auth-service",
        "severity": "HIGH",
        "alert": "Redis OOM error",
        "logs": "OOM command not allowed"
    })
    inc_id = res.json()["data"]["id"]
    
    # WORKED feedback
    res_fb1 = client.post(f"/api/incidents/{inc_id}/feedback", json={
        "recommendation": "Configure maxmemory policy volatile-lru",
        "feedback_type": "WORKED",
        "feedback_text": "Successfully reduced memory footprint"
    })
    assert res_fb1.status_code == 200
    
    # DID_NOT_WORK without actual_fix should fail
    res_fb_bad = client.post(f"/api/incidents/{inc_id}/feedback", json={
        "recommendation": "Restart pod",
        "feedback_type": "DID_NOT_WORK"
    })
    assert res_fb_bad.status_code == 400
    
    # DID_NOT_WORK with actual_fix
    res_fb2 = client.post(f"/api/incidents/{inc_id}/feedback", json={
        "recommendation": "Restart pod",
        "feedback_type": "DID_NOT_WORK",
        "feedback_text": "Pod restarted but memory filled again",
        "actual_fix": "Increased Redis cluster maxmemory from 2GB to 8GB"
    })
    assert res_fb2.status_code == 200

def test_resolve_incident():
    res = client.post("/api/incidents", json={
        "title": "Kafka Consumer Lag",
        "service_name": "notification-service",
        "severity": "HIGH",
        "alert": "Consumer lag > 100k",
        "logs": "Lag spike on topic user-events"
    })
    inc_id = res.json()["data"]["id"]
    
    res_resolve = client.post(f"/api/incidents/{inc_id}/resolve", json={
        "root_cause": "SendGrid API throttling consumer thread loop",
        "root_cause_category": "kafka_consumer_lag",
        "resolution_steps": "Increased partition count and worker pods",
        "outcome": "SUCCESS",
        "resolution_time_minutes": 20,
        "runbook_name": "kafka_consumer_lag_triage.md"
    })
    assert res_resolve.status_code == 200
    assert res_resolve.json()["data"]["status"] == "RESOLVED"

def test_claim_validation():
    valid_ids = ["INC-2026-001", "INC-2026-002"]
    llm_output = {
        "likely_root_cause": "Pool exhaustion",
        "historical_evidence_used": ["INC-2026-001", "INC-HALLUCINATED-999"]
    }
    validated = validate_historical_claims(llm_output, valid_ids)
    assert validated["historical_evidence_used"] == ["INC-2026-001"]
