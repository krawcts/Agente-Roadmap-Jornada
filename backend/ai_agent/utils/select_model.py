import sys
from loguru import logger

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
        logger.error("Nenhuma chave de API encontrada nas variáveis de ambiente (HF_TOKEN, OPENAI_TOKEN, DEEPSEEK_TOKEN).")
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
    print("--------------------")
    for letter, name in letter_mapping.items():
        if name in available_models:
            print(f" [{letter}] {name.capitalize()}")
            # logger.info(f"{letter} - {name}") # Use print for user interaction
            available_letters.append(letter)
    print("--------------------")

    while True:
        try:
            choice = input(f"Digite a letra do modelo ({'/'.join(available_letters)}): ").lower().strip()
            if choice in available_letters and letter_mapping[choice] in available_models:
                model_name = letter_mapping[choice]
                token = available_models[model_name]
                logger.info(f"Modelo selecionado: {model_name}")
                return model_name, token
            else:
                valid_options = '/'.join(available_letters)
                logger.warning(f"Escolha inválida. Use uma das opções: {valid_options}")
        except EOFError: # Handle Ctrl+D or unexpected end of input
             logger.error("Entrada cancelada.")
             sys.exit(1)
        except KeyboardInterrupt: # Handle Ctrl+C
             logger.error("Seleção interrompida pelo usuário.")
             sys.exit(1)