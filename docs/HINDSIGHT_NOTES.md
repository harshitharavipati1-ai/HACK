# Hindsight Vectorize Memory Integration Notes

## Overview
Hindsight (by Vectorize.io) is an agent-focused long-term memory system designed to retain, recall, and reflect on agent experiences and domain knowledge.

- **Docs Link**: [https://hindsight.vectorize.io/](https://hindsight.vectorize.io/)
- **SDK Package**: `hindsight-client` (Python)
- **Core Operations**:
  - `retain(bank_id, content, metadata, timestamp, context)`: Extracts entities, facts, and relationships to retain structured experience.
  - `recall(bank_id, query, ...)`: Executes hybrid multi-strategy retrieval (semantic vector, BM25 keyword, graph traversal, temporal filter).
  - `reflect(bank_id, query, ...)`: Performs agentic synthesis over stored memories to provide reasoned insights and consolidated patterns.

## Memory Architecture & Taxonomy

### Memory Bank Strategy
- **Bank ID**: `acme-sre` (One isolated memory bank per organization / environment tier).

### Memory Types
1. `incident_resolution`: Complete historical incident containing problem narrative, alert payload, root cause, resolution steps, MTTR, and runbook details.
2. `feedback_outcome`: Recorded engineer feedback (`WORKED`, `PARTIALLY_WORKED`, `DID_NOT_WORK`) linked to specific recommendation applications.
3. `failed_fix_antipattern`: Retained when an attempted fix fails. Explicitly marks attempted actions as anti-patterns for specific error signatures.
4. `pattern_insight`: High-level reflections created periodically or on request, grouping common failure modes and verified resolution strategies.

### Tags & Metadata Schema
- `service`: Name of the microservice (e.g., `payment-api`, `auth-service`, `postgres-primary`).
- `severity`: Alert severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- `root_cause_category`: Categorized root cause (`connection_pool`, `memory_leak`, `redis_stampede`, `oauth_misconfig`, `slow_query`, `kafka_lag`).
- `error_signatures`: Extracted log error patterns (e.g., `503 Service Unavailable`, `ConnectionPoolExhausted`, `TimeoutException`).
- `environment`: Deployment tier (`production`, `staging`).
- `runbook`: Associated operational runbook name.
- `outcome`: Resolution outcome (`SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`).
- `memory_type`: One of the 4 defined memory types above.

## HindsightAdapter & Fallback Design
The backend relies entirely on an abstract `MemoryService` interface.
- `RealHindsightMemoryService`: Invokes `hindsight_client.Hindsight` client methods (`retain`, `recall`, `reflect`).
- `LocalMemoryService`: High-performance local fallback using TF-IDF + BM25 keyword matching and vector similarity calculations over SQLite database records.
- **Provider Status Indicator**: Frontend top navigation bar shows `Memory Provider: Hindsight (Active)` or `Memory Provider: Local Demo Fallback` dynamically based on backend connectivity status.
