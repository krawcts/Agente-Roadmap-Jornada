from pydantic import BaseModel, EmailStr, Field as PydanticField
from typing import List, Optional
import datetime

# --- Pydantic Models for API Request/Response ---

class PlanRequestData(BaseModel):
    """Data required to request a new study plan."""
    name: str
    email: EmailStr # Use Pydantic's email validation
    hours_per_day: int = PydanticField(..., description="Hours per day for studying", gt=0, le=8) # Added description, validation remains
    available_days: List[str] = PydanticField(..., description="List of days available for study (e.g., ['Monday', 'Wednesday'])")
    start_date: datetime.date
    objectives: str = PydanticField(..., description="Main learning objectives")
    secondary_goals: Optional[str] = PydanticField(None, description="Secondary goals or topics") # Explicitly set default to None

    # Example for model configuration if needed later
    class Config:
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "hours_per_day": 3,
                "available_days": ["Monday", "Tuesday", "Thursday"],
                "start_date": "2024-05-15",
                "objectives": "Learn FastAPI basics",
                "secondary_goals": "Understand async programming"
            }
        }

class PlanResponse(BaseModel):
    """Response returned after successfully generating a plan."""
    message: str
    student_id: int
    plan_id: int
    generated_plan: str

    # Example for model configuration if needed later
    class Config:
        schema_extra = {
            "example": {
                "message": "Study plan generated and saved successfully.",
                "student_id": 1,
                "plan_id": 5,
                "generated_plan": "Week 1: Focus on chapters 1-3..."
            }
        }