# src/main.py

from dotenv import load_dotenv
import sys
from loguru import logger
from prompt_maker import make_final_prompt
from config import MODEL
from model_api import initialize_model, generate_response

# Carrega as variáveis de ambiente
load_dotenv()

try:
    # Inicializa o modelo
    model_name, token = initialize_model()
    
    # Gera o prompt final
    logger.info(f"Gerando prompt para o plano de estudos usando modelo {model_name}...")
    prompt_final = make_final_prompt()

    # Gera a resposta
    output = generate_response(model_name, token, prompt_final, MODEL["MAX_OUT_TOKENS"])

    logger.success("Plano de estudos gerado com sucesso!")
    print(output)
   
except Exception as e:
    logger.exception(f"Erro ao gerar o plano de estudos: {e}")
    sys.exit(1)