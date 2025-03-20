"""
Configurações centralizadas para o gerador de planos de estudo.
"""

# Configurações de arquivos
FILES = {
    "CONTENT": "conteudo_curso.json",
    "QUESTIONNAIRE": "questionario_aluno.json",
    "GUIDELINES": "guidelines.txt",
    "CALENDAR": "calendario_dados.json"
}

# Configurações do modelo de linguagem
MODEL = {
    "NAME": "meta-llama/Llama-3.2-3B-Instruct",
    "MAX_OUT_TOKENS": 1500,
}

# Configurações de validação
VALIDATION = {
    "REQUIRED_FIELDS": ["nivel_conhecimento", "horas_disponiveis", "data_inicio"]
}

# Templates de prompt (Opicional, pensando se vale a pena fazer isso)
TEMPLATES = {
    "TASK_INSTRUCTIONS": """
## TAREFA
Com base nas informações acima, crie um plano de estudos personalizado para o aluno.
O plano deve incluir:

1. Uma introdução personalizada ao aluno
2. Distribuição semanal de conteúdos
3. Estimativa de tempo para cada atividade
4. Marcos de progresso e pequenos objetivos alcançáveis

O plano deve respeitar o tempo disponível do aluno e seu nível de conhecimento.
"""
}