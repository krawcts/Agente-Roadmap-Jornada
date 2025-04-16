from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from sqlmodel import Session

from database.db_handler import get_session
from database.schemas import ContinueChatRequest, PlanResponse
from services.chat_service import ChatService
from dependencies import get_llm_service

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/continue", response_model=PlanResponse)
async def continue_chat(
    request_data: ContinueChatRequest, 
    session: Session = Depends(get_session),
    llm_service = Depends(get_llm_service)
):
    """
    Continues a conversation based on existing plan ID and message history.
    
    This endpoint:
    - Validates the chat request data
    - Ensures message history meets requirements
    - Delegates to ChatService for conversation continuation
    - Handles errors and returns appropriate HTTP responses
    """
    logger.info(f"Received chat continuation request for plan ID: {request_data.plan_id}")
    logger.debug(f"Message history contains {len(request_data.messages)} messages")
    
    # Validate chat history requirements
    if not request_data.messages:
        logger.warning(f"Empty message history received for plan ID: {request_data.plan_id}")
        raise HTTPException(status_code=400, detail="Chat history cannot be empty.")
        
    if request_data.messages[-1]['role'] != 'user':
        logger.warning(f"Last message not from user for plan ID: {request_data.plan_id}")
        raise HTTPException(status_code=400, detail="Last message must be from the user.")

    try:
        # Call service layer to handle business logic
        logger.debug(f"Calling ChatService to continue conversation for plan ID: {request_data.plan_id}")
        result = ChatService.continue_conversation(
            plan_id=request_data.plan_id,
            messages=request_data.messages,
            session=session,
            llm_service=llm_service
        )
        
        # Handle case where service returns None (plan not found)
        if not result:
            logger.warning(f"Plan with ID {request_data.plan_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Study plan with ID {request_data.plan_id} not found.")
        
        # Log success and return formatted response
        logger.info(f"Successfully continued chat for plan ID: {request_data.plan_id}")
        logger.debug(f"Updated chat now has {len(result.get('chat', []))} messages")
        return PlanResponse(**result)
    
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions without modification
        raise http_exc
    except Exception as e:
        # Log unexpected errors with full context
        logger.error(f"Error during chat continuation for plan ID {request_data.plan_id}: {e}", exc_info=True)
        logger.debug(f"Last user message: {request_data.messages[-1].get('content', '')[:100]}...")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the chat message.")