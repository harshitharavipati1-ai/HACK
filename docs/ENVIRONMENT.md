# Environment Assessment & Technology Stack Decisions

## System Environment
- **Node.js**: `v22.20.0`
- **npm**: `10.9.3`
- **Python**: `3.13.11`
- **Docker**: Not running / system local execution mode enabled
- **OS**: Windows (PowerShell environment)

## Chosen Stack & Package Versions

### Backend
- **Python Framework**: FastAPI (`0.115.0`)
- **ASGI Server**: Uvicorn (`0.30.0`)
- **ORMs & Schema**: SQLAlchemy (`2.0.35`), Pydantic (`2.9.0`), Pydantic-Settings (`2.5.0`)
- **Database**: SQLite (`sqlite:///./incident_memory.db`) with full PostgreSQL compatibility layer
- **Vector / Fallback Engine**: Scikit-Learn TF-IDF + Cosine Similarity + Keyword/Signature Matching for `LocalMemoryService` fallback
- **Hindsight SDK**: `hindsight-client` (`0.2.x`)
- **LLM Provider**: Groq API (`groq` package / OpenAI-compatible API) with Pydantic JSON parser & retry fallback mechanism

### Frontend
- **Framework**: Next.js (14.2.x App Router, React 18, TypeScript)
- **Styling**: Tailwind CSS (Dark theme SRE aesthetic) + Custom CSS variables + Lucide Icons (`lucide-react`)
- **Data Visualization**: Recharts (`2.12.x`)
- **HTTP Client**: Axios / Native Fetch with standard API envelopes

## Design Decisions
1. **Local & Cloud Hybrid Strategy**: Default to `LocalMemoryService` when `HINDSIGHT_API_KEY` or `HINDSIGHT_BASE_URL` is unconfigured/unreachable, gracefully auto-switching to `RealHindsightMemoryService` when valid credentials are provided. UI explicitly displays current active provider status.
2. **Deterministic Fallback Engine**: Local memory engine implements TF-IDF vector similarity with custom domain weighting (matching error signatures, service tags, and previous fix success weight).
3. **Structured & Narrative Hybrid Storage**: Incidents are retained both as structured metadata JSON and as narrative context paragraphs to maximize semantic recall accuracy.
