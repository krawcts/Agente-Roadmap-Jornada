import os
import sys
from loguru import logger
from ai_agent.utils.select_model import select_model
from ai_agent.llm_services.openai_client import OpenAIService
from ai_agent.llm_services.deepseek_client import DeepSeekService
from ai_agent.llm_services.openrouter_client import OpenRouterService
from ai_agent.llm_services.base_client import BaseLLMService


def initialize_llm_service() -> BaseLLMService:
    """
    Identifica as chaves de API disponíveis, seleciona o serviço
    e retorna a instância Singleton do cliente LLM correspondente.

    Returns:
        BaseLLMService: A instância Singleton do serviço LLM selecionado.
                       Retorna None se a inicialização falhar.
    """
    # Obtém tokens das variáveis de ambiente
    openai_token = os.getenv('OPENAI_API_KEY')
    deepseek_token = os.getenv('DEEPSEEK_API_KEY')
    openrouter_token = os.getenv('OPENROUTER_API_KEY')

    # Seleciona o modelo e obtém o token
    model_name, token = select_model(openai_token, deepseek_token, openrouter_token)

    # Obtém a instância Singleton do serviço apropriado
    llm_service_instance = None
    try:
        logger.info(f"Inicializando serviço para {model_name}...")
        if model_name == 'openai':
            # Calling OpenAIService() will return the Singleton instance
            llm_service_instance = OpenAIService(api_key=token)
        elif model_name == 'deepseek':
            # Calling DeepSeekService() will return the Singleton instance
            llm_service_instance = DeepSeekService(api_key=token)
        elif model_name == 'openrouter': # Added
            # Calling OpenRouterService() will return the Singleton instance
            llm_service_instance = OpenRouterService(api_key=token)
        else:
            # This case should ideally not be reached due to select_model logic
            logger.error(f"Tentativa de inicializar modelo desconhecido: {model_name}")
            sys.exit(1) # Exit if model name is somehow invalid

        # Check if initialization inside the singleton actually succeeded
        if not llm_service_instance or not getattr(llm_service_instance, '_initialized', False):
             # The __init__ inside the singleton should raise an error if it fails,
             # but double-check here just in case.
             logger.error(f"Falha ao inicializar o serviço {model_name}. Verifique os logs e a chave de API.")
             sys.exit(1)

        logger.success(f"Serviço {llm_service_instance.name} pronto.") # Use the name property
        return llm_service_instance

    except (ValueError, ConnectionError, Exception) as e:
         logger.error(f"Erro durante a inicialização do serviço {model_name}: {e}")
         # Exit because the service couldn't be initialized
         sys.exit(1)