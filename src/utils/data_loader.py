import os
import json
import csv

def get_data_dir():
    """Retorna o caminho para o diretório de dados """
    # Caminho para a pasta data relativo ao diretório raiz do projeto
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')   
    return data_dir

def load_file(filename, file_type=None):
    """
    Carrega um arquivo de texto ou JSON do diretório de dados.
    
    Args:
        filename (str): Nome do arquivo a ser carregado
        file_type (str, optional): Tipo do arquivo ('txt' ou 'json'). 
                                  Se None, será determinado pela extensão.
    
    Returns:
        O conteúdo do arquivo como string (txt) ou objeto (json), ou None em caso de erro.
    """
    # Lista de tipos de arquivo suportados
    SUPPORTED_TYPES = ['txt', 'json']
    
    data_dir = get_data_dir()
    file_path = os.path.join(data_dir, filename)
    
    # Determina o tipo de arquivo pela extensão se não for especificado
    if file_type is None:
        _, extension = os.path.splitext(filename)
        file_type = extension.lower().replace('.', '')
    
    # Verifica se o tipo de arquivo é suportado
    if file_type not in SUPPORTED_TYPES:
        print(f"Erro: Tipo de arquivo '{file_type}' não suportado. Tipos suportados: {', '.join(SUPPORTED_TYPES)}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if file_type == 'json':
                content = json.load(file)
                print(f"Arquivo JSON '{filename}' carregado com sucesso.")
            else:  # assume txt
                content = file.read()
                print(f"Arquivo de texto '{filename}' carregado com sucesso.")
            return content
    except FileNotFoundError:
        print(f"Arquivo '{filename}' não encontrado em {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON do arquivo '{filename}'. Formato inválido.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o arquivo '{filename}': {str(e)}")
        return None