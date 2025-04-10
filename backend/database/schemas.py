from pydantic import BaseModel, EmailStr, Field as PydanticField 
from typing import Dict, List, Optional  
import datetime  
from enum import Enum

# --- Definir Enums ---  
class SkillLevel(str, Enum):  
    NUNCA_UTILIZEI = "Nunca utilizei"  
    INICIANTE = "Iniciante"  
    INTERMEDIARIO = "Intermediário"  
    AVANCADO = "Avançado"  

class Weekday(str, Enum):  
    SEGUNDA = "Segunda"  
    TERCA = "Terça"  
    QUARTA = "Quarta"  
    QUINTA = "Quinta"  
    SEXTA = "Sexta"  
    SABADO = "Sábado"  
    DOMINGO = "Domingo"

# --- Pydantic Models for API Request/Response ---

class PlanRequestData(BaseModel):  
    name: str  
    email: EmailStr  
    # Usar o Enum Weekday como chave do dicionário  
    hours_per_day: Dict[Weekday, int] = PydanticField(  
        ...,  
        description="Horas de estudo por dia da semana (e.g. {'Segunda': 3, 'Terça': 2})"  
    )  
    start_date: datetime.date  
    python_level: SkillLevel  
    sql_level: SkillLevel  
    cloud_level: SkillLevel  
    used_git: bool  
    used_docker: bool  
    interests: Optional[List[str]] = None  
    main_challenge: Optional[str] = None

    class Config:
        use_enum_values = True # Necessário para usar os valores string dos Enums na API/Schema
        schema_extra = {
            "example": {
                "name": "João Silva",
                "email": "joao.silva@example.com",
                "hours_per_day": {
                    "Segunda": 3,
                    "Terça": 2,
                    "Quarta": 3,
                    "Quinta": 2,
                    "Sexta": 1,
                    "Sábado": 0,
                    "Domingo": 0
                },
                "start_date": "2024-05-15",
                "python_level": "Iniciante",
                "sql_level": "Nunca utilizei",
                "cloud_level": "Intermediário",
                "used_git": True,
                "used_docker": False,
                "interests": ["FastAPI", "Terraform"],
                "main_challenge": "Migrar aplicação para a nuvem"
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