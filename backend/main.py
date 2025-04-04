from fastapi import FastAPI, HTTPException, Depends
from loguru import logger
from contextlib import asynccontextmanager
from sqlmodel import Session # Import Session type hint
import sys
import os

# Adjust imports based on the new structure
from database.db_handler import get_session, create_db_and_tables, get_or_create_student, add_study_plan
from ai_agent.llm_service import initialize_llm_service
from ai_agent.prompt_maker import make_final_prompt
from database.schemas import PlanRequestData, PlanResponse

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    - Creates database and tables on startup.
    - Handles potential errors during startup.
    """
    logger.info("Application lifespan startup...")
    try:
        # Startup logic: Create database tables
        # This function already contains logging and basic error handling
        create_db_and_tables()
        logger.info("Database and tables checked/created successfully.")
    except Exception as e:
        # Log critical error if DB setup fails and prevent app from fully starting
        logger.critical(f"CRITICAL: Failed to initialize database during startup: {e}", exc_info=True)
        # Optionally re-raise to completely stop FastAPI startup,
        #If DB is unavailable.
        raise RuntimeError("Database initialization failed") from e

    yield # Application runs here

    # Shutdown logic (optional, e.g., close connections if not managed elsewhere)
    logger.info("Application lifespan shutdown...")
    # Add any cleanup code here if needed


# --- FastAPI App Initialization ---
# Pass the lifespan context manager to the FastAPI app
app = FastAPI(
    title="Study Plan Generator API",
    description="API to generate personalized study plans using AI.",
    version="1.0.0",
    lifespan=lifespan # Use the new lifespan manager
)

# --- Dependency Injection for LLM Service ---
# Initialize LLM service once when the app starts (using Singleton pattern within initialize_llm_service)
llm_service = None # Initialize as None first
try:
    llm_service = initialize_llm_service()
    logger.info("LLM Service initialized successfully for FastAPI app.")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize LLM Service on app startup: {e}", exc_info=True)

# --- API Endpoints ---
@app.post("/generate_plan", response_model=PlanResponse)
async def generate_study_plan(request_data: PlanRequestData, session: Session = Depends(get_session)):
    """
    Receives user data, generates a study plan using LLM, saves data, and returns the plan.
    """
    logger.info(f"Received request to generate plan for email: {request_data.email}")

    # Check if LLM Service was initialized successfully
    if llm_service is None:
        logger.error("LLM Service is not available (failed during initialization).")
        # Use 503 Service Unavailable
        raise HTTPException(status_code=503, detail="AI Service is currently unavailable. Please try again later.")

    try:
        # 1. Get or Create Student in DB
        # Use the session provided by Depends(get_session)
        student = get_or_create_student(session=session, name=request_data.name, email=request_data.email)

        # 2. Prepare data for prompt maker (convert Pydantic model to dict)
        # Ensure date is in the correct format if needed by prompt_maker
        api_data_for_prompt = request_data.model_dump()
        # Remove email from the data sent to the LLM for privacy/security
        if 'email' in api_data_for_prompt:
            api_data_for_prompt.pop('email')
            logger.debug("Removed email from data sent to LLM for privacy") 
        
        # 3. Create the Prompt
        logger.info("Generating final prompt...")
        # Pass the dictionary directly to make_final_prompt
        final_prompt = make_final_prompt(user_data=api_data_for_prompt)
        logger.debug(f"Generated Prompt Snippet:\n{final_prompt[:300]}...")

        # 4. Call the LLM
        logger.info("Sending prompt to LLM for completion...")
        generated_plan_text = llm_service.chat_completion(final_prompt)
        logger.info("Successfully received response from LLM.")

        if not generated_plan_text:
            logger.warning("LLM returned an empty response.")
            raise HTTPException(status_code=500, detail="AI failed to generate a plan. Please try again.")

        # 5. Save the Study Plan to DB
        plan_save_data = api_data_for_prompt.copy() # Start with input data
        plan_save_data["generated_plan"] = generated_plan_text # Add the generated plan

        new_plan = add_study_plan(session=session, student_id=student.id, plan_data=plan_save_data)

        # 6. Return Success Response (Commit happens automatically via get_session context manager)
        logger.success(f"Successfully generated and saved plan ID {new_plan.id} for student ID {student.id}")
        return PlanResponse(
            message="Study plan generated and saved successfully.",
            student_id=student.id,
            plan_id=new_plan.id,
            generated_plan=generated_plan_text
        )

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        raise http_exc
    except Exception as e:
        logger.error(f"Error during plan generation for {request_data.email}: {e}", exc_info=True)
        # Don't expose internal error details to the client
        raise HTTPException(status_code=500, detail="An internal error occurred while generating the study plan.")

@app.get("/")
async def read_root():
    return {"message": "Study Plan Generator API is running."}