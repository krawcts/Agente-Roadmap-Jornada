from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
from prompt_maker import make_final_prompt

# Carrega as variáveis de ambiente
load_dotenv()
HF_TOKEN = os.getenv('HF_TOKEN')

# Gera o prompt final
prompt_final = make_final_prompt()

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