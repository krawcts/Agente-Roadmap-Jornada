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
        response = client.text_generation(
            prompt, 
            max_new_tokens=max_tokens)
        return response
    elif model_name == 'openai':
        response = client.chat.completions.create(
            model=model_specific_name,
            messages=[
                {"role": "developer", "content": "Você é um expert em planejamento. Preste atenção nas instruções a seguir."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=max_tokens,
            stream=False)
        return response.choices[0].message.content
    elif model_name == 'deepseek':
        response = client.chat.completions.create(
            model=model_specific_name,
            messages=[
                {"role": "system", "content": "Você é um expert em planejamento. Preste atenção nas instruções a seguir."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            stream=False
        )
        return response.choices[0].message.content
    else:
        raise ValueError(f"Modelo desconhecido: {model_name}")


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
        huggingface_client = InferenceClient(
            model=model_specific_name,
            token=token
        )
        return huggingface_client
    elif model_name == 'openai':
        openai_client = OpenAI(api_key=token)
        return openai_client
    elif model_name == 'deepseek':
        # Supondo que a biblioteca deepseek tenha uma API similar
        deepseek_client = OpenAI(
            api_key=token,
            base_url="https://api.deepseek.com"
        )
        return deepseek_client
    else:
        raise ValueError(f"Modelo desconhecido: {model_name}")