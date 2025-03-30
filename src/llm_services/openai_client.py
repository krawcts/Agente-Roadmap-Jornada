import json
from openai import OpenAI
from loguru import logger

# Constantes
MODEL = "gpt-3.5-turbo"
SYSTEM_PROMPT = """
Você é um assistente IA útil e eficiente. Responda de forma clara e concisa,
mantendo um tom profissional e amigável.
"""
MAX_COMPLETION_TOKENS = 1500

class OpenAIService:
    def __init__(self, api_key=None):
        """
        Inicializa o serviço OpenAI.
        
        Args:
            api_key (str): Chave de API para OpenAI
        """
        # Configuração inicial com a chave da API fornecida
        self.api_key = api_key
        
        if not self.api_key:
            logger.error("API key da OpenAI não fornecida!")
            raise ValueError("API key da OpenAI é obrigatória")
            
        self.client = OpenAI(
            api_key=self.api_key
        )
        
        self.default_model = MODEL
        self.system_prompt = SYSTEM_PROMPT
        

        logger.add("openai.log", rotation="1 MB")  # Configura arquivo de log
        logger.info(f"Cliente OpenAI inicializado com o modelo {self.default_model}")

    def chat_completion(self, chat_history: list, system_prompt: str = None) -> str:    
        """
        Gera uma resposta do modelo com base em um histórico de chat.
        
        Args:
            chat_history (list): Lista de mensagens no formato {'role': X, 'content': Y}
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
                messages=request_payload,
                max_completion_tokens=MAX_COMPLETION_TOKENS
            )  
            return completion.choices[0].message.content
        except Exception as e:  
            logger.error("Erro na requisição: {}", str(e))  
            logger.error("Payload causador do erro:\n{}",  
                json.dumps(request_payload, indent=2, ensure_ascii=False))  
            return f"Erro ao processar a requisição: {str(e)}"