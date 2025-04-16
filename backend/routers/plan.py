from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from sqlmodel import Session

from database.db_handler import get_session
from database.schemas import PlanRequestData, PlanResponse
from services.plan_service import PlanService
from dependencies import get_llm_service

router = APIRouter(prefix="/plan", tags=["plans"])

@router.post("/generate", response_model=PlanResponse)
async def generate_study_plan(
    request_data: PlanRequestData, 
    session: Session = Depends(get_session),
    llm_service = Depends(get_llm_service)
):
    """
    Receives user data, generates a study plan using LLM, saves data, and returns the plan.
    
    This endpoint:
    - Validates incoming user data via PlanRequestData schema
    - Delegates plan generation to PlanService
    - Handles errors and returns appropriate HTTP responses
    """
    # Log request information but protect sensitive data
    logger.info(f"Received plan generation request for: {request_data.name} ({request_data.email})")
    logger.debug(f"Study area: {request_data.study_area}, Level: {request_data.level}")

    try:
        # Call service layer to handle business logic
        logger.debug("Calling PlanService to generate study plan")
        result = PlanService.generate_study_plan(
            request_data=request_data.model_dump(),
            session=session,
            llm_service=llm_service
        )
        
        # Handle case where service returns None (LLM failed)
        if not result:
            logger.warning(f"Plan generation failed for {request_data.email} - LLM returned empty response")
            raise HTTPException(status_code=500, detail="AI failed to generate a plan. Please try again.")
        
        # Log success and return formatted response
        logger.info(f"Successfully generated plan for {request_data.email}")
        logger.debug(f"Returning response with plan_id: {result.get('plan_id')}")
        return PlanResponse(**result)
    
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions without modification
        raise http_exc
    except Exception as e:
        # Log unexpected errors with full context
        logger.error(f"Error during plan generation for {request_data.email}: {e}", exc_info=True)
        logger.debug(f"Request data that caused error: {request_data.model_dump()}")
        raise HTTPException(status_code=500, detail="An internal error occurred while generating the study plan.")