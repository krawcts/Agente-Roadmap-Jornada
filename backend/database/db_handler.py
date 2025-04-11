from sqlmodel import SQLModel, create_engine, Session, select
from typing import List, Dict
from contextlib import contextmanager
from pathlib import Path
from loguru import logger
import os

from database.models import Student, StudyPlan 

# --- Database Path Configuration ---
# Determine the database directory based on environment
# Default to the directory containing this file if DATABASE_DIR_PATH is not set (for local execution)
# In Docker, set the DATABASE_DIR_PATH environment variable to /app/database
_DATABASE_DIR_PATH_STR = os.getenv("DATABASE_DIR_PATH")

if _DATABASE_DIR_PATH_STR:
    # Use the path from the environment variable (Docker)
    DATABASE_DIR = Path(_DATABASE_DIR_PATH_STR)
    logger.info(f"Using database directory from environment variable: {DATABASE_DIR}")
else:
    # Default to a data directory at the project root for local execution
    # __file__ is the path to the current script (db_handler.py)
    # .resolve() makes the path absolute
    # .parent.parent gets the backend directory (parent of database)
    # .parent gets the project root directory (parent of backend)
    # / 'data' navigates to the data directory at the project root
    DATABASE_DIR = Path(__file__).resolve().parent.parent.parent / 'data'
    logger.info(f"DATABASE_DIR_PATH not set, defaulting to project data directory: {DATABASE_DIR}")


DATABASE_FILE = DATABASE_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create the engine (connection pool)
# connect_args is specific to SQLite to disable same-thread check for FastAPI background tasks if needed
# For simple sequential requests, it might not be strictly necessary, but good practice.
logger.info(f"Connecting to database at: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """Creates the database file and tables if they don't exist."""
    logger.info(f"Ensuring database and tables exist at {DATABASE_FILE}...")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database and tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database or tables: {e}", exc_info=True)
        raise # Re-raise the exception to indicate failure

def get_session():
    """Provides a transactional scope around a series of operations."""
    session = Session(engine)
    try:
        yield session
        session.commit()
        logger.debug("DB Session committed.")
    except Exception as e:
        logger.error(f"DB Session rollback due to error: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug("DB Session closed.")

# --- CRUD Operations ---

def get_or_create_student(session: Session, name: str, email: str) -> Student:
    """Gets a student by email or creates a new one."""
    logger.info(f"Getting or creating student with email: {email}")
    statement = select(Student).where(Student.email == email)
    student = session.exec(statement).first()
    if not student:
        logger.info(f"Student not found, creating new student: {name} ({email})")
        student = Student(name=name, email=email)
        session.add(student)
        # Commit is handled by the context manager, but need to refresh to get ID
        session.flush() # Assigns ID without committing transaction yet
        session.refresh(student)
        logger.info(f"Created student with ID: {student.id}")
    else:
        logger.info(f"Found existing student with ID: {student.id}")
        # Optionally update name if it differs?
        if student.name != name:
            student.name = name
            session.add(student)
            session.flush()
            session.refresh(student)
    return student

def add_study_plan(session: Session, student_id: int, plan_data: dict) -> StudyPlan:
    """Adds a new study plan for a given student."""
    logger.info(f"Adding study plan for student ID: {student_id}")
    logger.debug(f"Plan data: {plan_data}")

    # Map incoming plan_data (should match Streamlit form structure) to the new model fields
    new_plan = StudyPlan(
        student_id=student_id,
        start_date=plan_data["start_date"], # Assumes it's already a date object from API layer
        weekly_availability=plan_data["hours_per_day"], # Renamed in form/payload, maps to this field
        python_level=plan_data["python_level"],
        sql_level=plan_data["sql_level"],
        cloud_level=plan_data["cloud_level"],
        used_git=plan_data["used_git"], # Should be boolean
        used_docker=plan_data["used_docker"], # Should be boolean
        interests=plan_data.get("interests"), # Optional list
        main_challenge=plan_data.get("main_challenge"), # Optional string
        chat=plan_data["chat"] # Corrected to get chat history from 'chat' key
    )
    session.add(new_plan)
    session.flush() # Assign ID
    session.refresh(new_plan)
    logger.info(f"Added new study plan with ID: {new_plan.id}")
    return new_plan


def update_chat(session: Session, plan_id: int, conversation_history: List[Dict[str, str]]) -> StudyPlan | None:
    """Updates the conversation history snapshot for a specific study plan."""
    logger.info(f"Updating conversation history snapshot for plan ID: {plan_id}")
    plan = session.get(StudyPlan, plan_id) # Use session.get for primary key lookup
    if plan:
        plan.chat = conversation_history # Use the renamed field 'chat'
        session.add(plan)
        session.flush() # Apply changes to the session
        session.refresh(plan) # Refresh the object with DB state (including potential triggers/defaults)
        logger.info(f"Successfully updated conversation snapshot for plan ID: {plan_id}")
        return plan
    else:
        logger.warning(f"Study plan with ID {plan_id} not found during update attempt.")
        return None