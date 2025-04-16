from fastapi import FastAPI, HTTPException, Depends
from loguru import logger
from contextlib import asynccontextmanager
from sqlmodel import Session 


# Adjust imports based on the new structure
from ai_agent.llm_services.base_client import BaseLLMService
from database.db_handler import get_session, create_db_and_tables, get_or_create_student, add_study_plan, update_chat
from ai_agent.llm_service import initialize_llm_service
from ai_agent.prompt_maker import make_final_prompt
from database.schemas import PlanRequestData, PlanResponse, ContinueChatRequest

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    - Creates database and tables on startup.
    - Initializes LLM service.
    - Handles potential errors during startup.
    """
    logger.info("Application lifespan startup...")
    try:
        # Startup logic: Create database tables
        create_db_and_tables()
        logger.info("Database and tables checked/created successfully.")
        
        # Inicializar o LLM service e armazená-lo no estado da aplicação
        logger.info("Initializing LLM service...")
        app.state.llm_service = initialize_llm_service()
        logger.info("LLM Service initialized successfully for FastAPI app.")
        
    except Exception as e:
        logger.critical(f"CRITICAL: Failed during application startup: {e}", exc_info=True)
        raise RuntimeError("Application initialization failed") from e

    yield  # Application runs here

    # Shutdown logic
    logger.info("Application lifespan shutdown...")
    # Aqui você pode adicionar lógica de limpeza, se necessário


# --- FastAPI App Initialization ---
# Pass the lifespan context manager to the FastAPI app
app = FastAPI(
    title="Study Plan Generator API",
    description="API to generate personalized study plans using AI.",
    version="1.0.0",
    lifespan=lifespan # Use the new lifespan manager
)

# --- Dependency para acessar o LLM Service ---
def get_llm_service(app=Depends()) -> BaseLLMService:
    """Provides access to the LLM service singleton."""
    if not hasattr(app.state, "llm_service") or app.state.llm_service is None:
        logger.error("LLM Service is not available (failed during initialization).")
        raise HTTPException(status_code=503, detail="AI Service is currently unavailable. Please try again later.")
    return app.state.llm_service

# --- API Endpoints ---
@app.post("/generate_plan", response_model=PlanResponse)
async def generate_study_plan(
    request_data: PlanRequestData, 
    session: Session = Depends(get_session),
    llm_service: BaseLLMService = Depends(get_llm_service)  # Adicionado dependência
):
    """
    Receives user data, generates a study plan using LLM, saves data, and returns the plan.
    """
    logger.info(f"Received request to generate plan for email: {request_data.email}")

    try:
        # 1. Get or Create Student in DB
        student = get_or_create_student(session=session, name=request_data.name, email=request_data.email)

        # 2. Prepare data for prompt maker (convert Pydantic model to dict)
        api_data_for_prompt = request_data.model_dump()
        # Remove email from the data sent to the LLM for privacy/security
        if 'email' in api_data_for_prompt:
            api_data_for_prompt.pop('email')
        logger.debug("Removed email from data sent to LLM for privacy") 
        
        # 3. Create the Prompt
        logger.info("Generating final prompt...")
        final_prompt = make_final_prompt(user_data=api_data_for_prompt)
        logger.debug(f"Generated Prompt Snippet:\n{str(final_prompt)[:200]}...")

        # 4. Call the LLM
        logger.info("Sending initial prompt to LLM for plan generation...")
        initial_messages = [{"role": "user", "content": final_prompt}]
        # Use a instância injetada do llm_service
        assistant_response_text = llm_service.chat_completion(messages=initial_messages)
        logger.info("Successfully received initial plan response from LLM.")

        if not assistant_response_text:
            logger.warning("LLM returned an empty response.")
            raise HTTPException(status_code=500, detail="AI failed to generate a plan. Please try again.")

        # 5. Save the Study Plan to DB
        plan_save_data = api_data_for_prompt.copy()
        initial_conversation_history = initial_messages + [{"role": "assistant", "content": assistant_response_text}]
        plan_save_data["chat"] = initial_conversation_history

        new_plan = add_study_plan(session=session, student_id=student.id, plan_data=plan_save_data)

        # 6. Return Success Response
        logger.success(f"Successfully generated and saved plan ID {new_plan.id} for student ID {student.id}")
        return PlanResponse(
            message="Study plan generated and saved successfully.",
            student_id=student.id,
            plan_id=new_plan.id,
            chat=initial_conversation_history
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error during plan generation for {request_data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while generating the study plan.")


@app.get("/")
async def read_root():
    return {"message": "Study Plan Generator API is running."}


@app.post("/continue_chat", response_model=PlanResponse)
async def continue_chat(
    request_data: ContinueChatRequest, 
    session: Session = Depends(get_session),
    llm_service: BaseLLMService = Depends(get_llm_service)  # Adicionado dependência
): 
    """
    Continues a conversation based on existing plan ID and current message history,
    using PlanResponse as both input and output schema.
    """
    logger.info(f"Received request to continue chat for plan ID: {request_data.plan_id}")
    current_chat_history = request_data.messages
    logger.debug(f"Received chat history Snippet: {str(current_chat_history)[:200]}...")

    if not current_chat_history:
        raise HTTPException(status_code=400, detail="Chat history cannot be empty.")
    if current_chat_history[-1]['role'] != 'user':
        raise HTTPException(status_code=400, detail="Last message in the history must be from the user.")

    # Remova a verificação explícita - a dependência já faz isso
    # if llm_service is None: ...

    try:
        # 1. Call the LLM with the provided message history
        logger.info(f"Sending conversation history to LLM for plan ID: {request_data.plan_id}...")
        # Use a instância injetada do llm_service
        assistant_response_text = llm_service.chat_completion(messages=request_data.messages)
        logger.info(f"Successfully received chat response from LLM for plan ID: {request_data.plan_id}.")

        # O restante do código permanece igual
        if not assistant_response_text:
            logger.warning(f"LLM returned an empty response for plan ID: {request_data.plan_id}.")
            raise HTTPException(status_code=500, detail="AI failed to generate a response. Please try again.")

        updated_chat_history = request_data.messages + [{"role": "assistant", "content": assistant_response_text}]
        logger.debug(f"Updated chat history Snippet for plan ID {request_data.plan_id}: {str(updated_chat_history)[:200]}...")

        updated_plan = update_chat(
            session=session,
            plan_id=request_data.plan_id,
            conversation_history=updated_chat_history
        )

        if not updated_plan:
            logger.error(f"Failed to find plan ID {request_data.plan_id} during update after chat.")
            raise HTTPException(status_code=404, detail=f"Study plan with ID {request_data.plan_id} not found.")

        logger.success(f"Successfully continued chat and updated snapshot for plan ID {request_data.plan_id}")
        return PlanResponse(
            message="Chat continued successfully.",
            student_id=updated_plan.student_id,
            plan_id=request_data.plan_id,
            chat=updated_chat_history
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error during chat continuation for plan ID {request_data.plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the chat message.")