from fastapi import Depends, HTTPException
from loguru import logger

from ai_agent.llm_services.base_client import BaseLLMService

# Global application reference - will be updated when the application initializes
_app = None

def get_app():
    """
    Retrieves the FastAPI application instance.
    
    Returns:
        The FastAPI application instance or None if not set.
    """
    if _app is None:
        logger.debug("Application reference requested but not yet initialized")
    return _app

def set_app(app):
    """
    Sets the global FastAPI application reference.
    
    This function should be called once during application startup
    to enable dependency functions to access application state.
    
    Args:
        app: FastAPI application instance
    """
    global _app
    logger.debug(f"Setting global application reference: {app}")
    _app = app
    logger.debug("Global application reference successfully set")

def get_llm_service() -> BaseLLMService:
    """
    Provides access to the LLM service singleton.
    
    This dependency:
    - Retrieves the LLM service from application state
    - Verifies the service is available and properly initialized
    - Raises appropriate HTTP exceptions when the service is unavailable
    
    Returns:
        BaseLLMService: The initialized LLM service for generating responses
        
    Raises:
        HTTPException: When LLM service is not available or properly initialized
    """
    app = get_app()
    
    # Check if app is available
    if not app:
        logger.error("Cannot access LLM service: Application reference not set")
        raise HTTPException(
            status_code=503, 
            detail="Application not fully initialized. Please try again later."
        )
    
    # Check if llm_service exists in app state
    if not hasattr(app.state, "llm_service"):
        logger.error("LLM Service not found in application state")
        raise HTTPException(
            status_code=503, 
            detail="AI Service initialization incomplete. Please try again later."
        )
    
    # Check if llm_service is properly initialized
    if app.state.llm_service is None:
        logger.error("LLM Service is null in application state")
        raise HTTPException(
            status_code=503, 
            detail="AI Service is currently unavailable. Please try again later."
        )
        
    logger.debug("LLM Service successfully retrieved from application state")
    return app.state.llm_service