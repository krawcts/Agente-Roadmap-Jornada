from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
import sys
from loguru import logger
from prompt_maker import make_final_prompt
from config import MODEL

# Carrega as variáveis de ambiente
load_dotenv()
HF_TOKEN = os.getenv('HF_TOKEN')

if not HF_TOKEN:
    logger.error("Token HF_TOKEN não encontrado nas variáveis de ambiente.")
    sys.exit(1)

try:
    # Gera o prompt final
    logger.info("Gerando prompt para o plano de estudos...")
    prompt_final = make_final_prompt()

    # Inicializa o cliente de inferência
    logger.info("Inicializando cliente de inferência com a API Hugging Face...")
    client = InferenceClient(
        MODEL["NAME"],
        token=f"{HF_TOKEN}",
    )

    logger.info("Enviando prompt para o modelo e aguardando resposta...")
    output = client.text_generation(
        prompt_final,
        max_new_tokens=MODEL["MAX_OUT_TOKENS"],
    )

    logger.success("Plano de estudos gerado com sucesso!")
    print(output)
   
except RuntimeError as e:
    logger.error(f"Erro ao gerar o plano de estudos: {e}")
    sys.exit(1)
except Exception as e:
    logger.exception("Erro inesperado durante a execução")
    sys.exit(1)