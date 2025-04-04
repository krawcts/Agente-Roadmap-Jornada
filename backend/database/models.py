from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import datetime
from sqlalchemy import Text  # Importe o tipo Text do SQLAlchemy

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True) # Unique identifier
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship: One student can have many study plans
    study_plans: List["StudyPlan"] = Relationship(back_populates="student")

class StudyPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True) # Link to Student table
    hours_per_day: int
    available_days: str # Store as comma-separated string or JSON string
    start_date: datetime.date
    objectives: str = Field(sa_type=Text()) # Use TEXT para strings longas
    secondary_goals: Optional[str] = Field(default=None, sa_type=Text())
    generated_plan: str = Field(sa_type=Text()) # Armazena o plano completo
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship: Each study plan belongs to one student
    student: Student = Relationship(back_populates="study_plans")