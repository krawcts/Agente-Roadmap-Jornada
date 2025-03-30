import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class DeepseekService:
    def __init__(self):
        # Configuração inicial com a chave da OpenAI
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),base_url="https://api.deepseek.com")
        self.default_model = "deepseek-chat"
        self.system_prompt = """
        Você é um assistente IA útil. Responda de forma clara e concisa,
        mantendo um tom profissional e amigável.
        """

    logger.add("deepseek.log", rotation="1 MB")  # Configura arquivo de log

    def chat_completion(self, chat_history: list, system_prompt: str = None) -> str:    
        """Gera uma resposta do modelo de linguagem com base na entrada do usuário.
            
        Args:
            user_input (str): Texto de entrada do usuário
            system_prompt (str, optional): Prompt personalizado. Defaults para o prompt padrão.
            
        Returns:
            str: Resposta gerada pelo modelo
        """  
        try:  
            # Log do histórico recebido  
            logger.debug("Histórico recebido RAW:\n{}",  
                        json.dumps(chat_history, indent=2, ensure_ascii=False))
            # Estrutura correta exigida pela API  
            messages = [{  
                "role": "system",  
                "content": system_prompt or self.system_prompt  
            }]  

            valid_messages = []  
            for idx, msg in enumerate(chat_history):  
                if not isinstance(msg, dict):  
                    logger.warning("Mensagem inválida (não é dicionário) no índice {}: {}", idx, msg)  
                    continue  

                if "role" not in msg or "content" not in msg:  
                    logger.warning("Estrutura inválida no índice {}: {}", idx, msg)  
                    continue  

                if msg["role"] not in ["user", "assistant"]:  
                    logger.warning("Role inválido no índice {}: {}", idx, msg["role"])  
                    continue  

                valid_messages.append({  
                    "role": str(msg["role"]),  
                    "content": str(msg["content"])  
                })  

            logger.debug("Mensagens válidas processadas:\n{}",  
                        json.dumps(valid_messages, indent=2, ensure_ascii=False))  

            request_payload = messages + valid_messages  
            logger.info("Enviando request para API:\n{}",  
                       json.dumps(request_payload, indent=2, ensure_ascii=False))  

            completion = self.client.chat.completions.create(  
                model=self.default_model,  
                messages=request_payload  
            )  
            return completion.choices[0].message.content
        except Exception as e:  
            logger.error("Erro na requisição: {}", str(e))  
            logger.error("Payload causador do erro:\n{}",  
                        json.dumps(request_payload, indent=2, ensure_ascii=False))  
            return f"Erro ao processar a requisição: {str(e)}"

# Instância singleton para ser usada na aplicação
deepseek_service = DeepseekService()