from loguru import logger
from sqlmodel import Session

from database.db_handler import update_chat
from ai_agent.llm_services.base_client import BaseLLMService

class ChatService:
    @staticmethod
    def continue_conversation(plan_id, messages, session: Session, llm_service: BaseLLMService):
        """
        Continue a conversation with existing plan and message history.
        
        Parameters:
            plan_id (int): ID of the study plan to continue conversation with
            messages (list): List of message objects with role and content
            session (Session): Database session for persistence operations
            llm_service (BaseLLMService): Service to interact with the LLM
            
        Returns:
            dict: Response data with updated conversation, or None if failure
        """
        logger.debug(f"Continuing conversation for plan ID: {plan_id}")
        logger.debug(f"Received {len(messages)} messages in conversation history")
        
        # 1. Call the LLM with the provided message history
        logger.info(f"Sending conversation to LLM for plan ID: {plan_id}")
        # We pass the full conversation history to maintain context
        assistant_response_text = llm_service.chat_completion(messages=messages)
        
        # Check if we got a valid response
        if not assistant_response_text:
            logger.warning(f"LLM returned empty response for plan ID: {plan_id}")
            return None

        logger.info(f"Received LLM response with length: {len(assistant_response_text)} characters")

        # 2. Update chat history and save to database
        logger.debug("Updating conversation history with new assistant response")
        updated_chat_history = messages + [
            {"role": "assistant", "content": assistant_response_text}
        ]
        
        # 3. Persist the updated conversation in the database
        logger.debug(f"Saving updated conversation to database for plan ID: {plan_id}")
        updated_plan = update_chat(
            session=session,
            plan_id=plan_id,
            conversation_history=updated_chat_history
        )

        # Check if the plan exists in the database
        if not updated_plan:
            logger.warning(f"Plan with ID {plan_id} not found in database")
            return None

        logger.info(f"Successfully updated conversation for plan ID: {plan_id}")

        # 4. Prepare and return response data
        logger.debug("Preparing response data with updated conversation")
        return {
            "message": "Chat continued successfully.",
            "student_id": updated_plan.student_id,
            "plan_id": plan_id,
            "chat": updated_chat_history
        }