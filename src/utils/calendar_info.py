from datetime import datetime, timedelta
from src.utils.data_loader import load_file

def get_calendar_info(questionario_aluno=None):
    """
    Processa informações de calendário com base na data de início do questionário.
    
    Args:
        questionario_aluno (dict): Dicionário com as respostas do questionário do aluno,
                                  incluindo a data de início desejada.
    
    Returns:
        str: Texto formatado com informações de calendário para o prompt da LLM.
    """
    # Carrega informações de feriados e eventos do arquivo JSON
    calendario_dados = load_file('calendario_dados.json')
    
    return calendario_dados
