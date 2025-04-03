from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.prompt_maker import make_final_prompt
from backend.llm_service import initialize_llm_service
from loguru import logger
import os
from dotenv import load_dotenv
import datetime

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="Agente Roadmap Jornada API",
    description="API para geração de planos de estudo personalizados",
    version="1.0.0"
)

# Inicializar o serviço LLM na startup
llm_service = None
try:
    llm_service = initialize_llm_service()
    if not llm_service:
        logger.error("Não foi possível inicializar o serviço LLM.")
except Exception as e:
    logger.exception(f"Erro ao inicializar serviço LLM: {e}")

# Modelo de dados para a requisição
class StudyPlanRequest(BaseModel):
    name: str
    email: str
    hours_per_day: int
    available_days: List[str]
    start_date: str
    objectives: str
    secondary_goals: Optional[str] = None

# Modelo de dados para a resposta
class StudyPlanResponse(BaseModel):
    plan: str

@app.post("/generate-plan", response_model=StudyPlanResponse)
async def generate_plan(request: StudyPlanRequest):
    """Endpoint para gerar plano de estudos a partir dos dados do formulário."""
    try:
        if not llm_service:
            raise HTTPException(status_code=503, detail="Serviço LLM não disponível")
            
        logger.info("Gerando prompt final...")
        prompt_final = make_final_prompt(request.dict())
        
        logger.info("Enviando prompt para LLM...")
        generated_plan = llm_service.chat_completion(prompt_final)
        
        if not generated_plan:
            raise HTTPException(status_code=500, detail="Recebeu uma resposta vazia da IA")
            
        return {"plan": generated_plan}
        
    except Exception as e:
        logger.exception(f"Erro ao gerar plano: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Endpoint para verificar o status da API."""
    status = "ok" if llm_service else "service_unavailable"
    return {"status": status}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)