from huggingface_hub import InferenceClient

from dotenv import load_dotenv
import os

from utils.data_loader import load_file

# Carrega as variáveis de ambiente
load_dotenv()
HF_TOKEN = os.getenv('HF_TOKEN')

# ---------- CARREGAMENTO DOS DADOS ----------
# Carrega o conteúdo do curso 
conteudo_curso = load_file('conteudo_curso.json')
if not conteudo_curso:
    print("Erro: Não foi possível carregar o conteúdo do curso.")
    exit(1)

# Carrega as respostas do questionário do aluno
questionario_aluno = load_file('questionario_aluno.json')
if not questionario_aluno:
    print("Erro: Não foi possível carregar o questionário do aluno.")
    exit(1)

# Carrega as guidelines para criação do plano de estudos
guidelines = load_file('guidelines.txt')
if not guidelines:
    print("Erro: Não foi possível carregar as guidelines.")
    exit(1)

# ---------- MONTAGEM DO PROMPT ----------
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

# ---------- PROMPT FINAL E CHAMADA DA API ----------
# Combinação de todos os prompts em um único prompt final
prompt_final = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{prompt_conteudo_curso}

{prompt_questionario}

{prompt_guidelines}

{prompt_instrucoes}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

# Inicializa o cliente de inferência
client = InferenceClient(
    "meta-llama/Llama-3.2-3B-Instruct",
    token=f"{HF_TOKEN}",

)

output = client.text_generation(
    prompt_final,
    max_new_tokens=1500,
)

print(output)