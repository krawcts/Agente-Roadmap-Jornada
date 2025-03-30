import os
import sys
from openai import OpenAI
from loguru import logger
from huggingface_hub import InferenceClient
from config import MODEL


def initialize_model():
    """
    Inicializa o modelo com base nas chaves de API disponíveis.

    Returns:
        tuple: (model_name, token) O nome do modelo selecionado e sua chave de API
    """
    # Obtém tokens das variáveis de ambiente
    hf_token = os.getenv('HF_TOKEN')
    openai_token = os.getenv('OPENAI_TOKEN')
    deepseek_token = os.getenv('DEEPSEEK_TOKEN')

    # Seleciona o modelo
    model_name, token = select_model(hf_token, openai_token, deepseek_token)
    llm_service = initialize_llm_service(model_name, token)
    return llm_service

def select_model(hf_token, openai_token, deepseek_token):
    """
    Seleciona um modelo de inferência com base nas chaves de API disponíveis.

    Args:
        hf_token: Token da Hugging Face
        openai_token: Token da OpenAI
        deepseek_token: Token da DeepSeek

    Returns:
        tuple: (model_name, token) O nome do modelo selecionado e sua chave de API
    """
    # Mapeia tokens para modelos
    model_map = {
        'huggingface': hf_token,
        'openai': openai_token,
        'deepseek': deepseek_token
    }

    # Filtra modelos disponíveis (com token)
    available_models = {name: token for name, token in model_map.items() if token}

    if not available_models:
        logger.error("Nenhuma chave de API encontrada nas variáveis de ambiente.")
        sys.exit(1)

    # Escolha automática se só tiver um modelo
    if len(available_models) == 1:
        model_name = next(iter(available_models))
        token = available_models[model_name]
        logger.info(f"Usando modelo {model_name} (única opção disponível)")
        return model_name, token

    # Solicita escolha do usuário
    logger.info("Múltiplos modelos disponíveis. Escolha um digitando a letra correspondente:")

    # Mapeia letras para modelos
    letter_mapping = {
        'h': 'huggingface',
        'o': 'openai',
        'd': 'deepseek'
    }

    # Mostra apenas os modelos disponíveis
    available_letters = []
    for letter, name in letter_mapping.items():
        if name in available_models:
            logger.info(f"{letter} - {name}")
            available_letters.append(letter)

    while True:
        choice = input("Digite a letra do modelo (h/o/d): ").lower()
        if choice in available_letters and letter_mapping[choice] in available_models:
            model_name = letter_mapping[choice]
            token = available_models[model_name]
            return model_name, token
        else:
            valid_options = '/'.join(available_letters)
            logger.error(f"Escolha inválida. Use uma das opções: {valid_options}")

def initialize_llm_service(model_name, token):
    """
    Inicializa o serviço LLM com base no nome do modelo e no token fornecido.

    Args:
        model_name: Nome do modelo ('huggingface', 'openai', 'deepseek')
        token: Token de API para o modelo

    Returns:
        object: Instância do serviço LLM inicializado
    """
    if model_name == 'huggingface':
        from llm_services.huggingface_client import HuggingFaceService
        return HuggingFaceService(api_key=token)
    elif model_name == 'openai':
        from llm_services.openai_client import OpenAIService
        return OpenAIService(api_key=token)
    elif model_name == 'deepseek':
        from llm_services.deepseek_client import DeepSeekService
        return DeepSeekService(api_key=token)
    else:
        raise ValueError(f"Modelo desconhecido: {model_name}")