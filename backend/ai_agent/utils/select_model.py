import sys
from loguru import logger

def select_model(openai_token: str | None, deepseek_token: str | None, openrouter_token: str | None):
    """
    Seleciona automaticamente um serviço LLM com base na disponibilidade e prioridade das chaves de API.

    Prioridade: OpenAI > DeepSeek > OpenRouter

    Args:
        openai_token (str | None): Token da API OpenAI.
        deepseek_token (str | None): Token da API DeepSeek.
        openrouter_token (str | None): Token da API OpenRouter.

    Returns:
        tuple: (model_name, token) O nome do modelo selecionado e sua chave de API
    """
    # Define a ordem de prioridade e os tokens correspondentes
    priority_order = [
        ('openai', openai_token),
        ('deepseek', deepseek_token),
        ('openrouter', openrouter_token),
        # Removido 'huggingface'
    ]

    # Encontra o primeiro serviço disponível na ordem de prioridade
    selected_service = None
    for name, token in priority_order:
        if token:
            selected_service = (name, token)
            break # Para no primeiro encontrado

    if not selected_service:
        logger.error("Nenhuma chave de API encontrada para OpenAI, DeepSeek ou OpenRouter nas variáveis de ambiente (OPENAI_API_KEY, DEEPSEEK_TOKEN, OPENROUTER_API_KEY).")
        sys.exit(1) # Sai se nenhum serviço estiver configurado

    model_name, token = selected_service
    logger.info(f"Seleção automática: Usando serviço {model_name.capitalize()} com base na prioridade e disponibilidade da chave.")
    return model_name, token

# --- Lógica de seleção manual removida ---
#
#    # Escolha automática se só tiver um modelo
#    if len(available_models) == 1:
#        model_name = next(iter(available_models))
#        token = available_models[model_name]
#        logger.info(f"Usando modelo {model_name} (única opção disponível)")
#        return model_name, token
#
#    # Solicita escolha do usuário
#    logger.info("Múltiplos modelos disponíveis. Escolha um digitando a letra correspondente:")
#
#    # Mapeia letras para modelos
#    letter_mapping = {
#        'h': 'huggingface',
#        'o': 'openai',
#        'd': 'deepseek'
#    }
#
#    # Mostra apenas os modelos disponíveis
#    available_letters = []
#    print("--------------------")
#    for letter, name in letter_mapping.items():
#        if name in available_models:
#            print(f" [{letter}] {name.capitalize()}")
#            # logger.info(f"{letter} - {name}") # Use print for user interaction
#            available_letters.append(letter)
#    print("--------------------")
#
#    while True:
#        try:
#            choice = input(f"Digite a letra do modelo ({'/'.join(available_letters)}): ").lower().strip()
#            if choice in available_letters and letter_mapping[choice] in available_models:
#                model_name = letter_mapping[choice]
#                token = available_models[model_name]
#                logger.info(f"Modelo selecionado: {model_name}")
#                return model_name, token
#            else:
#                valid_options = '/'.join(available_letters)
#                logger.warning(f"Escolha inválida. Use uma das opções: {valid_options}")
#        except EOFError: # Handle Ctrl+D or unexpected end of input
#             logger.error("Entrada cancelada.")
#             sys.exit(1)
#        except KeyboardInterrupt: # Handle Ctrl+C
#             logger.error("Seleção interrompida pelo usuário.")
#             sys.exit(1)
