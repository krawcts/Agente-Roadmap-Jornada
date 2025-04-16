from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager
import time

from database.db_handler import create_db_and_tables
from ai_agent.llm_service import initialize_llm_service
import dependencies
from routers import plan, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    
    This context manager:
    - Sets up all required resources when the application starts
    - Ensures proper cleanup when the application shuts down
    - Handles any errors during startup with appropriate logging
    """
    start_time = time.time()
    logger.info("=== Application startup process beginning ===")
    
    try:
        # 1. Create database tables
        logger.info("Initializing database tables...")
        create_db_and_tables()
        logger.success("Database tables successfully initialized")
        
        # 2. Initialize LLM service
        logger.info("Initializing Language Model service...")
        app.state.llm_service = initialize_llm_service()
        logger.success("LLM service successfully initialized and ready")
        
        # Log successful startup
        elapsed = time.time() - start_time
        logger.success(f"=== Application startup completed successfully in {elapsed:.2f} seconds ===")
        
    except Exception as e:
        # Log detailed error information on startup failure
        logger.critical(f"!!! CRITICAL STARTUP FAILURE: {e}", exc_info=True)
        logger.critical("Application cannot start due to initialization errors")
        raise RuntimeError("Application initialization failed") from e

    # Application runs here
    yield  

    # Shutdown cleanup
    logger.info("=== Application shutdown process beginning ===")
    # Add any resource cleanup here if needed in the future
    logger.info("=== Application shutdown completed ===")

# FastAPI App Initialization
app = FastAPI(
    title="Study Plan Generator API",
    description="API to generate personalized study plans using AI.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register app instance in dependency manager for proper service access
logger.debug("Registering application instance in dependency manager")
dependencies.set_app(app)

# Root endpoint for health check and API verification
@app.get("/", tags=["health"])
async def read_root():
    """
    Root endpoint that confirms API is operational.
    Used for health checks and basic connectivity testing.
    """
    logger.debug("Health check endpoint accessed")
    return {
        "message": "Study Plan Generator API is running.",
        "status": "operational",
        "version": app.version
    }

# Register all router modules
logger.info("Registering API routers...")
app.include_router(plan.router)
app.include_router(chat.router)
logger.debug("API routers successfully registered")

# Log application readiness
logger.info(f"Application initialized and ready to accept requests")
logger.info(f"API documentation available at /docs and /redoc")