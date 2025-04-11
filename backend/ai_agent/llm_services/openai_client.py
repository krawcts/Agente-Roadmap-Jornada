import os
import threading
from typing import List, Dict
from openai import OpenAI, OpenAIError 
from loguru import logger
from ai_agent.llm_services.base_client import BaseLLMService

class OpenAIService(BaseLLMService):
    """
    Singleton implementation for the OpenAI API client.

    Uses the official OpenAI Python library to interact with the API.
    Requires the OPENAI_API_KEY environment variable or an api_key passed
    during the first instantiation.
    """

    _MODEL = "gpt-4o-mini"

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    logger.debug("Creating new OpenAIService instance")
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None, default_model: str = _MODEL):
        """
        Initializes the OpenAIService Singleton.

        Args:
            api_key (str, optional): OpenAI API key. If None, attempts to read
                                     from OPENAI_API_KEY environment variable.
                                     Defaults to None.
            default_model (str, optional): The default OpenAI model to use if
                                           not specified in chat_completion kwargs.
                                           Defaults to "gpt-3.5-turbo".

        Raises:
            ValueError: If no API key is provided or found in environment variables.
            ConnectionError: If the OpenAI client fails to initialize (e.g., invalid key).
        """
        if self._initialized:
            return

        with self._lock:
            if self._initialized: # Double-check after acquiring lock
                return

            logger.info("Initializing OpenAIService...")
            resolved_api_key = api_key or os.getenv('OPENAI_API_KEY') # Prioritize passed key

            if not resolved_api_key:
                logger.error("OpenAI API key not provided and not found in OPENAI_API_KEY environment variable.")
                raise ValueError("OpenAI API key is required for initialization.")

            self.api_key = resolved_api_key # Store the key if needed later, though client uses it directly
            self.default_model = default_model

            try:
                # Initialize the official OpenAI client
                self.client = OpenAI(api_key=self.api_key)
                logger.success(f"OpenAI client initialized successfully. Default model: {self.default_model}")
                self._initialized = True
            except OpenAIError as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                # Reset instance if initialization fails? Consider implications.
                # OpenAIService._instance = None
                raise ConnectionError(f"Failed to initialize OpenAI Client: {e}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during OpenAI client initialization: {e}")
                raise ConnectionError(f"Unexpected error initializing OpenAI Client: {e}") from e

    @property
    def name(self) -> str:
        """Returns the service name."""
        return "openai"

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generates a chat completion using the OpenAI API based on a list of messages.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries,
                                             e.g., [{"role": "user", "content": "Hello"}].
            **kwargs: Additional keyword arguments for the OpenAI API call, such as:
                - model (str): Override the default model (e.g., "gpt-4").
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


        if not self._initialized or not self.client:
            raise RuntimeError("OpenAIService is not initialized.")

        model = kwargs.get("model", self.default_model)
        logger.debug(f"Sending messages to OpenAI model {model}...")

        # Filter kwargs to pass only valid parameters to the OpenAI API
        valid_api_keys = {
            'temperature', 'max_tokens', 'top_p', 'frequency_penalty',
            'presence_penalty', 'stop', 'stream' # Add others if needed
        }
        api_kwargs = {k: v for k, v in kwargs.items() if k in valid_api_keys}

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **api_kwargs
            )
            logger.debug("Received response from OpenAI")

            # Extract the message content
            if response.choices:
                content = response.choices[0].message.content
                return content.strip() if content else ""
            else:
                logger.warning("OpenAI response did not contain any choices.")
                return "" # Return empty string if no choices are available

        except OpenAIError as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise # Re-raise the specific OpenAI error
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenAI API call: {e}")
            raise RuntimeError(f"Unexpected error during OpenAI chat completion: {e}") from e