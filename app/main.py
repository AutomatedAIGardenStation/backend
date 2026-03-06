import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from app.config import settings
from app.core.security import INITIAL_CONFIG_HASH, compute_config_hash, verify_config_drift

logger = logging.getLogger("garden_station")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # API Startup Validation
    logger.info("Starting Garden Station Backend...")

    # 1. Validate Secret Key
    if settings.secret_key == "default-unsafe-secret-key-change-in-production":
        if settings.environment == "production":
            logger.error("Default secret key detected in production environment. Refusing to start.")
            raise RuntimeError("Missing secure secret_key in production configuration.")
        else:
            logger.warning("Using default unsafe secret key. This is not recommended outside development.")

    # 2. Check Database URL exists
    if not settings.database_url:
        logger.error("Missing database URL configuration.")
        raise ValueError("database_url must be provided.")

    # 3. Ensure configuration hasn't drifted since load time (Zero-trust check)
    current_hash = compute_config_hash()
    if current_hash != INITIAL_CONFIG_HASH:
        logger.error("Configuration drift detected during startup validation.")
        raise RuntimeError("Zero-trust validation failed: Configuration changed unexpectedly.")

    logger.info(f"Configuration validated successfully for environment: {settings.environment}")
    yield
    # Shutdown actions could go here
    logger.info("Shutting down Garden Station Backend...")

app = FastAPI(
    title="Garden Station Backend",
    lifespan=lifespan,
    dependencies=[Depends(verify_config_drift)]
)

@app.get("/")
async def read_root():
    return {"status": "Backend Orchestrator Running"}
