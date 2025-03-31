from utils.data_loader import load_file
from utils.calendar_info import get_calendar_info
from loguru import logger
from config import FILES

def make_final_prompt():
    """
    Carrega os dados necessários e cria o prompt final para o modelo.
    
    Returns:
        str: Prompt formatado pronto para ser enviado ao modelo.
    """
        # ---- CARREGAMENTO DOS DADOS ----
    try:
        # Carrega o conteúdo do curso
        conteudo_curso = load_file(FILES["CONTENT"])
        if not conteudo_curso:
            raise FileNotFoundError("Conteúdo do curso não encontrado ou vazio")

        # Carrega as respostas do questionário do aluno
        questionario_aluno = load_file(FILES["QUESTIONNAIRE"])
        if not questionario_aluno:
            raise FileNotFoundError("Questionário do aluno não encontrado ou vazio")

        # Carrega as guidelines para criação do plano de estudos
        guidelines = load_file(FILES["GUIDELINES"])
        if not guidelines:
            raise FileNotFoundError("Guidelines não encontradas ou vazias")

        # Obtém informações de calendário com base no questionário
        try:
            calendario_info = get_calendar_info(questionario_aluno)
        except Exception as e:
            logger.error(f"Erro ao processar informações de calendário: {e}")
            calendario_info = "## INFORMAÇÕES DE CALENDÁRIO\nNão foi possível obter informações detalhadas de calendário."

    except FileNotFoundError as e:
        logger.error(f"Erro crítico ao carregar dados: {e}")
        logger.error("Não é possível continuar sem os arquivos essenciais.")
        raise RuntimeError(f"Falha ao inicializar o gerador de plano de estudos: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado durante o carregamento de dados: {e}")
        raise RuntimeError(f"Erro inesperado: {e}")

    # ---- MONTAGEM DO PROMPT ----
    # Prompt para introduzir o conteúdo do curso
    prompt_conteudo_curso = f"""
    ## CONTEÚDO DO CURSO
    O curso contém os seguintes materiais e aulas:

    {conteudo_curso}
    """

    # Prompt para introduzir o questionário do aluno
    prompt_questionario = f"""
    ## PERFIL DO ALUNO
    O aluno forneceu as seguintes informações no questionário:

    {questionario_aluno}
    """

    # Prompt com informações de calendário
    prompt_calendario = calendario_info

    # Prompt para introduzir as guidelines
    prompt_guidelines = f"""
    ## GUIDELINES PARA O PLANO DE ESTUDOS
    As seguintes diretrizes devem ser seguidas na criação do plano:

    {guidelines}
    """

    # Prompt com instruções para o modelo
    prompt_instrucoes = """
    ## TAREFA
    Com base nas informações acima, crie um plano de estudos personalizado para o aluno.
    O plano deve incluir:

    1. Uma introdução personalizada ao aluno
    2. Distribuição semanal de conteúdos
    3. Estimativa de tempo para cada atividade
    4. Marcos de progresso e pequenos objetivos alcançáveis

    O plano deve respeitar o tempo disponível do aluno e seu nível de conhecimento.
    """

    # ---- PROMPT FINAL ----
    # Combinação de todos os prompts em um único prompt final
    prompt_final = f"""

    {prompt_instrucoes}

    {prompt_guidelines}

    {prompt_conteudo_curso}

    {prompt_calendario}

    {prompt_questionario}     

    """

    return prompt_final