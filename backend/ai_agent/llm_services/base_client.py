from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseLLMService(ABC):
    """  
    Classe Base Abstrata para clientes de serviço de Modelos de Linguagem Grande (LLM).  

    Define a interface comum que todas as implementações específicas de clientes LLM  
    (por exemplo, OpenAI, Hugging Face, DeepSeek) devem seguir. Isso garante  
    intercambialidade e uso consistente em toda a aplicação.  
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """  
        Retorna o nome identificador único do serviço LLM.  

        Isso deve ser implementado por cada subclasse para retornar uma string  
        específica como 'openai', 'huggingface', 'deepseek'.  

        Retorna:  
            str: O nome do serviço.  
        """
        raise NotImplementedError

    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        Gera uma resposta de chat baseada em uma lista de mensagens fornecida.

        Este é o método principal para interação de chat com o LLM. As subclasses
        devem implementar a lógica específica de chamada da API para seu respectivo serviço.

        Args:
            messages (List[Dict[str, str]]): Uma lista de dicionários representando o
                                             histórico da conversa, onde cada dicionário
                                             deve ter as chaves 'role' (e.g., 'system',
                                             'user', 'assistant') e 'content' (o texto
                                             da mensagem).
            **kwargs (Any): Argumentos de palavra-chave arbitrários que podem ser específicos
                            para a API LLM subjacente (por exemplo, temperatura,
                            max_tokens, nome do modelo, sequências de parada).
                            As implementações de subclasse devem lidar com os kwargs
                            relevantes para seu serviço.

        Retorna:  
            str: A resposta em texto gerada pelo LLM.  

        Levanta:  
            NotImplementedError: Se a subclasse não implementar este método.  
            Exception: As subclasses podem levantar exceções específicas relacionadas a erros  
                        de API, problemas de conexão, falhas de autenticação, etc.  
        """
        raise NotImplementedError
