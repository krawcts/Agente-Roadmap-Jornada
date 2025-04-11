from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict # Added Dict
import datetime
from sqlalchemy import Text, Column, JSON # Added Column, JSON

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
    start_date: datetime.date
    # Store weekly availability as JSON: {"Monday": 2, "Tuesday": 3, ...}
    weekly_availability: Dict[str, int] = Field(sa_column=Column(JSON))
    python_level: str
    sql_level: str
    cloud_level: str
    used_git: bool
    used_docker: bool
    interests: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    main_challenge: Optional[str] = Field(default=None, sa_type=Text())
    chat: List[Dict[str, str]] = Field(sa_column=Column(JSON)) # Renamed from generated_plan
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship: Each study plan belongs to one student
    student: Student = Relationship(back_populates="study_plans")