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