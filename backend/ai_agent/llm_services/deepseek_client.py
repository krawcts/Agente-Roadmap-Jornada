import os
import threading
from openai import OpenAI, OpenAIError # Reuse the OpenAI library
from loguru import logger
from ai_agent.llm_services.base_client import BaseLLMService

class DeepSeekService(BaseLLMService):
    """
    Singleton implementation for the DeepSeek API client.

    Uses the official OpenAI Python library configured for the DeepSeek API endpoint.
    Requires the DEEPSEEK_API_KEY environment variable or an api_key passed
    during the first instantiation.
    """

    _MODEL = "deepseek-chat"
    _DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    logger.debug("Creating new DeepSeekService instance")
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None, default_model: str = _MODEL):
        """
        Initializes the DeepSeekService Singleton.

        Args:
            api_key (str, optional): DeepSeek API key. If None, attempts to read
                                     from DEEPSEEK_API_KEY environment variable.
                                     Defaults to None.
            default_model (str, optional): The default DeepSeek model to use.
                                           Defaults to "deepseek-chat".

        Raises:
            ValueError: If no API key is provided or found in environment variables.
            ConnectionError: If the client fails to initialize (e.g., invalid key, wrong base URL).
        """
        if self._initialized:
            return

        with self._lock:
            if self._initialized: # Double-check after acquiring lock
                return

            logger.info("Initializing DeepSeekService...")
            resolved_api_key = api_key or os.getenv('DEEPSEEK_TOKEN')

            if not resolved_api_key:
                logger.error("DeepSeek API key not provided and not found in DEEPSEEK_API_KEY environment variable.")
                raise ValueError("DeepSeek API key is required for initialization.")

            self.api_key = resolved_api_key
            self.default_model = default_model

            try:
                # Initialize the OpenAI client, but point it to DeepSeek's API endpoint
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self._DEEPSEEK_BASE_URL
                )
                logger.success(f"DeepSeek client initialized successfully. Endpoint: {self._DEEPSEEK_BASE_URL}, Default model: {self.default_model}")
                self._initialized = True
            except OpenAIError as e: # Catch OpenAIError as the library is reused
                logger.error(f"Failed to initialize DeepSeek client (using OpenAI library): {e}")
                raise ConnectionError(f"Failed to initialize DeepSeek Client: {e}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during DeepSeek client initialization: {e}")
                raise ConnectionError(f"Unexpected error initializing DeepSeek Client: {e}") from e

    @property
    def name(self) -> str:
        """Returns the service name."""
        return "deepseek"

    def chat_completion(self, prompt: str, **kwargs) -> str:
        """
        Generates a chat completion using the DeepSeek API (via OpenAI library).

        Args:
            prompt (str): The user's input prompt.
            **kwargs: Additional keyword arguments compatible with the OpenAI/DeepSeek API, such as:
                - model (str): Override the default model (e.g., "deepseek-coder").
                - temperature (float): Sampling temperature.
                - max_tokens (int): Maximum number of tokens to generate.
                - top_p (float): Nucleus sampling parameter.
                - frequency_penalty (float): Penalty for frequent tokens.
                - presence_penalty (float): Penalty for new tokens.
                - stop (list[str]): List of stop sequences.

        Returns:
            str: The content of the generated message.

        Raises:
            RuntimeError: If the service is not initialized.
            OpenAIError: If the API call fails.
        """
        _SYSTEM_PROMPT = """
            Você é um assistente IA útil. Responda de forma clara e concisa,
            mantendo um tom profissional e amigável.
            """

        if not self._initialized or not self.client:
            raise RuntimeError("DeepSeekService is not initialized.")

        model = kwargs.get("model", self.default_model)
        logger.debug(f"Sending prompt to DeepSeek model {model} via endpoint {self._DEEPSEEK_BASE_URL}...")

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            ]

        # Filter kwargs valid for the API
        valid_api_keys = {
            'temperature', 'max_tokens', 'top_p', 'frequency_penalty',
            'presence_penalty', 'stop', 'stream'
        }
        api_kwargs = {k: v for k, v in kwargs.items() if k in valid_api_keys}

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **api_kwargs
            )
            logger.debug("Received response from DeepSeek")

            if response.choices:
                content = response.choices[0].message.content
                return content.strip() if content else ""
            else:
                logger.warning("DeepSeek response did not contain any choices.")
                return ""

        except OpenAIError as e: # Catch OpenAIError
            logger.error(f"DeepSeek API call failed: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during DeepSeek API call: {e}")
            raise RuntimeError(f"Unexpected error during DeepSeek chat completion: {e}") from e