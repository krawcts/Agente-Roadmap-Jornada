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


# Inicializa o cliente de inferência
client = InferenceClient(
    "meta-llama/Llama-3.2-3B-Instruct",
    token=f"{HF_TOKEN}",

)


prompt="""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

The capital of france is<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

output = client.text_generation(
    prompt,
    max_new_tokens=100,
)

print(output)