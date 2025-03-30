from dotenv import load_dotenv
import sys
from loguru import logger

from prompt_maker import make_final_prompt
from llm_service import initialize_llm_service

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configure Loguru (optional, but good practice)
logger.add("logs/agent_{time}.log", rotation="1 day", retention="7 days", level="DEBUG")
logger.info("Iniciando aplicação...")

try:
    # Inicializa e obtém a instância Singleton do serviço LLM
    llm_service = initialize_llm_service() 

    # Garante que llm_service não é None	
    if not llm_service:
        logger.error("Não foi possível inicializar o serviço LLM. Encerrando.")
        sys.exit(1) # Exit if service is None

    # Use the name property from the service instance
    logger.info(f"Gerando prompt para o plano de estudos usando modelo {llm_service.name}...")
    prompt_final = make_final_prompt()

    # Gera a resposta usando o método da instância do serviço
    logger.info("Enviando prompt para o LLM...")
    output = llm_service.chat_completion(prompt_final)

    logger.success("Plano de estudos gerado com sucesso!")
    print("\n--- PLANO DE ESTUDOS GERADO ---")
    print(output)
    print("--------------------------------\n")

except Exception as e:
    # Aqui são detectados erros durante a geração do prompt ou na própria chamada da API,
    # enquanto initialize_llm_service lida com erros de inicialização.
    
    logger.exception(f"Erro inesperado durante a execução: {e}")
    sys.exit(1)
except KeyboardInterrupt:
     logger.warning("Execução interrompida pelo usuário.")
     sys.exit(0)
finally:
    logger.info("Aplicação finalizada.")