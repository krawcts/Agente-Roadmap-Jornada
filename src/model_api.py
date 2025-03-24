import os
import sys
import openai
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
    return select_model(hf_token, openai_token, deepseek_token)

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

def generate_response(model_name, token, prompt, max_tokens):
    """
    Gera uma resposta usando o modelo especificado.
    
    Args:
    model_name: Nome do modelo ('huggingface', 'openai', 'deepseek')
    token: Token de API para o modelo
    prompt: Prompt para gerar a resposta
    max_tokens: Número máximo de tokens na resposta
    
    Returns:
    A resposta gerada pelo modelo
    """
    client = get_inference_client(model_name, token)
    
    # Obtém o nome específico do modelo da configuração
    model_specific_name = MODEL[f"{model_name.upper()}_MODEL"]
    
    if model_name == 'huggingface':
        return client.text_generation(prompt, max_new_tokens=max_tokens)
    elif model_name == 'openai':
        response = client.Completion.create(
            engine=model_specific_name,
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response.choices[0].text
    elif model_name == 'deepseek':
        return client.generate(prompt, max_tokens=max_tokens)

def get_inference_client(model_name, token):
    """
    Retorna um cliente de inferência com base no modelo escolhido.
    
    Args:
    model_name: Nome do modelo ('huggingface', 'openai', 'deepseek')
    token: Token de API para o modelo
    
    Returns:
    Um cliente de inferência para o modelo especificado
    """
    # Obtém o nome específico do modelo da configuração
    model_specific_name = MODEL[f"{model_name.upper()}_MODEL"]
    
    if model_name == 'huggingface':
        return InferenceClient(model_specific_name, token=token)
    elif model_name == 'openai':
        openai.api_key = token
        return openai
    elif model_name == 'deepseek':
        # Supondo que a biblioteca deepseek tenha uma API similar
        import deepseek
        return deepseek.Client(token=token)
    else:
        raise ValueError(f"Modelo desconhecido: {model_name}")