# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field as PydanticField
from typing import List, Optional
import datetime
from loguru import logger

# Adjust imports based on the new structure
from .database.db_handler import get_session, create_db_and_tables, get_or_create_student, add_study_plan
from .ai_agent.llm_service import initialize_llm_service
from .ai_agent.prompt_maker import make_final_prompt
from sqlmodel import Session # Import Session type hint

# --- Pydantic Models for API Request/Response ---
class PlanRequestData(BaseModel):
    name: str
    email: EmailStr # Use Pydantic's email validation
    hours_per_day: int = PydanticField(..., gt=0, le=8) # Add validation
    available_days: List[str]
    start_date: datetime.date
    objectives: str
    secondary_goals: Optional[str] = None

class PlanResponse(BaseModel):
    message: str
    student_id: int
    plan_id: int
    generated_plan: str

# --- FastAPI App Initialization ---
app = FastAPI(title="Study Plan Generator API")

# --- Dependency Injection for LLM Service ---
# Initialize LLM service once when the app starts (using Singleton pattern within initialize_llm_service)
try:
    llm_service = initialize_llm_service()
    logger.info("LLM Service initialized successfully for FastAPI app.")
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize LLM Service on app startup: {e}", exc_info=True)
    # Depending on severity, you might want the app to fail startup
    # raise RuntimeError("LLM Service failed to initialize") from e
    llm_service = None # Or set to None and handle in endpoint

@app.on_event("startup")
def on_startup():
    """Create database and tables when the FastAPI app starts."""
    logger.info("FastAPI app starting up...")
    create_db_and_tables()
    # You could also pre-initialize the LLM service here if not done above
    # global llm_service
    # if llm_service is None:
    #     try:
    #         llm_service = initialize_llm_service()
    #         logger.info("LLM Service initialized successfully during startup event.")
    #     except Exception as e:
    #         logger.critical(f"CRITICAL: Failed to initialize LLM Service during startup event: {e}", exc_info=True)


# --- API Endpoints ---
@app.post("/generate_plan", response_model=PlanResponse)
async def generate_study_plan(request_data: PlanRequestData, session: Session = Depends(get_session)):
    """
    Receives user data, generates a study plan using LLM, saves data, and returns the plan.
    """
    logger.info(f"Received request to generate plan for email: {request_data.email}")

    if llm_service is None:
        logger.error("LLM Service is not available.")
        raise HTTPException(status_code=503, detail="AI Service is currently unavailable. Please try again later.")

    try:
        # 1. Get or Create Student in DB
        # Use the session provided by Depends(get_session)
        student = get_or_create_student(session=session, name=request_data.name, email=request_data.email)

        # 2. Prepare data for prompt maker (convert Pydantic model to dict)
        # Ensure date is in the correct format if needed by prompt_maker
        api_data_for_prompt = request_data.model_dump() # Use model_dump in Pydantic v2+
        # api_data_for_prompt['start_date'] = request_data.start_date.strftime("%Y-%m-%d") # Already a date object, prompt_maker should handle

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