

def get_calendar_info(questionario_aluno=None):
    """
    Processa informações de calendário com base na data de início do questionário.
    
    Args:
        questionario_aluno (dict): Dicionário com as respostas do questionário do aluno,
                                  incluindo a data de início desejada.
    
    Returns:
        dict: Dicionário com informações processadas do calendário e texto formatado.
    """
    calendar_info = {
        "data_inicio_str": None,
        "feriados_no_periodo": [],
        "texto_formatado": ""  # Campo para armazenar o texto formatado para o prompt
    }

    return calendar_info