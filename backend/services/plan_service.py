from loguru import logger
from sqlmodel import Session

from database.db_handler import get_or_create_student, add_study_plan
from ai_agent.prompt_maker import make_final_prompt
from ai_agent.llm_services.base_client import BaseLLMService

class PlanService:
    @staticmethod
    def generate_study_plan(request_data, session: Session, llm_service: BaseLLMService):
        """
        Generate a study plan using LLM and save it to the database.
        
        Parameters:
            request_data (dict): Data from the user request containing name, email, and study preferences
            session (Session): Database session for persistence operations
            llm_service (BaseLLMService): Service to interact with the LLM

        Returns:
            dict: Response data containing plan details, or None if generation failed
        """
        logger.debug(f"Starting study plan generation process for user: {request_data.get('name')}")
        
        # 1. Get or Create Student in DB
        logger.debug(f"Checking if student exists in database: {request_data.get('email')}")
        student = get_or_create_student(
            session=session, 
            name=request_data['name'], 
            email=request_data['email']
        )
        logger.info(f"Using student with ID: {student.id} for plan creation")

        # 2. Prepare data for prompt maker - Remove sensitive info before sending to LLM
        logger.debug("Preparing data for prompt generation - removing sensitive fields")
        api_data_for_prompt = request_data.copy()
        if 'email' in api_data_for_prompt:
            api_data_for_prompt.pop('email')
            logger.debug("Email removed from prompt data for privacy")
        
        # 3. Create the Prompt using our prompt engineering template
        logger.debug("Generating prompt from user data")
        final_prompt = make_final_prompt(user_data=api_data_for_prompt)
        logger.debug(f"Generated prompt with length: {len(final_prompt)} characters")
        
        # 4. Call the LLM with our carefully crafted prompt
        logger.info("Sending prompt to LLM for study plan generation")
        initial_messages = [{"role": "user", "content": final_prompt}]
        assistant_response_text = llm_service.chat_completion(messages=initial_messages)
        
        # Check if we got a valid response from the LLM
        if not assistant_response_text:
            logger.warning("LLM returned empty response for study plan generation")
            return None

        logger.info(f"Received study plan from LLM with length: {len(assistant_response_text)} characters")

        # 5. Save the Study Plan to DB with chat history for continuity
        logger.debug("Preparing to save study plan to database")
        plan_save_data = api_data_for_prompt.copy()
        initial_conversation_history = initial_messages + [
            {"role": "assistant", "content": assistant_response_text}
        ]
        plan_save_data["chat"] = initial_conversation_history

        new_plan = add_study_plan(
            session=session, 
            student_id=student.id, 
            plan_data=plan_save_data
        )
        logger.info(f"Study plan saved to database with ID: {new_plan.id}")

        # 6. Prepare and return response data
        logger.debug("Preparing response data with plan details")
        return {
            "message": "Study plan generated and saved successfully.",
            "student_id": student.id,
            "plan_id": new_plan.id,
            "chat": initial_conversation_history
        }