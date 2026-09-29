import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.routers import incidents, webhooks, memory, analytics, eval, seed

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("incident-memory-agent")

# Create Database tables
Base.metadata.create_all(bind=engine)

# Auto-seed database if empty
from app.database import SessionLocal
from app.models import Incident
from app.routers.seed import seed_database

db_init = SessionLocal()
try:
    if db_init.query(Incident).count() == 0:
        logger.info("Database empty on startup. Auto-seeding 25 incidents & memory bank...")
        seed_database(db_init)
        logger.info("Auto-seeding complete.")
except Exception as e:
    logger.error(f"Auto-seeding failed: {e}")
finally:
    db_init.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler (ensures no unhandled stack traces are leaked)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal error occurred. Request logged securely."
            }
        }
    )

# Include Routers
app.include_router(incidents.router, prefix=settings.API_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_PREFIX)
app.include_router(memory.router, prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)
app.include_router(eval.router, prefix=settings.API_PREFIX)
app.include_router(seed.router, prefix=settings.API_PREFIX)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
