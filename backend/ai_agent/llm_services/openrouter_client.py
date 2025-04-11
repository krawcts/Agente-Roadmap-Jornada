import os
import threading
from typing import List, Dict, Optional
from openai import OpenAI, OpenAIError # Reuse the OpenAI library
from loguru import logger
from ai_agent.llm_services.base_client import BaseLLMService

class OpenRouterService(BaseLLMService):
    """
    Singleton implementation for the OpenRouter API client.

    Uses the official OpenAI Python library configured for the OpenRouter API endpoint.
    Requires the OPENROUTER_API_KEY environment variable or an api_key passed
    during the first instantiation.
    Optionally uses the OPENROUTER_MODEL environment variable to specify the model,
    otherwise falls back to a default model defined in _MODEL.
    """

    _MODEL = "openai/gpt-4o-mini"
    _OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    logger.debug("Creating new OpenRouterService instance")
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None, default_model: Optional[str] = None):
        """
        Initializes the OpenRouterService Singleton.

        Args:
            api_key (str, optional): OpenRouter API key. If None, attempts to read
                                     from OPENROUTER_API_KEY environment variable.
                                     Defaults to None.
            default_model (str, optional): Overrides the default model logic (env var/fallback).
                                           Defaults to None.

        Raises:
            ValueError: If no API key is provided or found in environment variables.
            ConnectionError: If the client fails to initialize.
        """
        if self._initialized:
            return

        with self._lock:
            if self._initialized: # Double-check after acquiring lock
                return

            logger.info("Initializing OpenRouterService...")
            resolved_api_key = api_key or os.getenv('OPENROUTER_API_KEY')

            if not resolved_api_key:
                logger.error("OpenRouter API key not provided and not found in OPENROUTER_API_KEY environment variable.")
                raise ValueError("OpenRouter API key is required for initialization.")

            # Determine the model: passed argument > environment variable > fallback
            if default_model:
                self.default_model = default_model
                logger.info(f"Using model passed during initialization: {self.default_model}")
            else:
                env_model = os.getenv('OPENROUTER_MODEL')
                if env_model:
                    self.default_model = env_model
                    logger.info(f"Using model from OPENROUTER_MODEL env var: {self.default_model}")
                else:
                    self.default_model = self._MODEL
                    logger.info(f"OPENROUTER_MODEL env var not set, using fallback model: {self.default_model}")

            self.api_key = resolved_api_key

            try:
                # Initialize the OpenAI client, pointing it to OpenRouter's API endpoint
                # Pass custom headers required/recommended by OpenRouter
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self._OPENROUTER_BASE_URL,
                )
                # Test connection (optional but recommended) - simple request like listing models
                # self.client.models.list() # This might incur a small cost or require specific permissions

                logger.success(f"OpenRouter client initialized successfully. Endpoint: {self._OPENROUTER_BASE_URL}, Default model: {self.default_model}")
                self._initialized = True
            except OpenAIError as e: # Catch OpenAIError as the library is reused
                logger.error(f"Failed to initialize OpenRouter client (using OpenAI library): {e}")
                raise ConnectionError(f"Failed to initialize OpenRouter Client: {e}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during OpenRouter client initialization: {e}")
                raise ConnectionError(f"Unexpected error initializing OpenRouter Client: {e}") from e

    @property
    def name(self) -> str:
        """Returns the service name."""
        return "openrouter"

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generates a chat completion using the OpenRouter API (via OpenAI library).

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries,
                                             e.g., [{"role": "user", "content": "Hello"}].
            **kwargs: Additional keyword arguments compatible with the OpenAI/OpenRouter API, such as:
                - model (str): Override the default model for this specific call.
                - temperature (float): Sampling temperature.
                - max_tokens (int): Maximum number of tokens to generate.
                - top_p (float): Nucleus sampling parameter.
                - frequency_penalty (float): Penalty for frequent tokens.
                - presence_penalty (float): Penalty for new tokens.
                - stop (list[str]): List of stop sequences.
                # OpenRouter specific params might exist, check their docs if needed.

        Returns:
            str: The content of the generated message.

        Raises:
            RuntimeError: If the service is not initialized.
            OpenAIError: If the API call fails.
        """
        if not self._initialized or not self.client:
            raise RuntimeError("OpenRouterService is not initialized.")

        # Use the instance's default model unless overridden in kwargs
        model = kwargs.get("model", self.default_model)
        logger.debug(f"Sending messages to OpenRouter model {model} via endpoint {self._OPENROUTER_BASE_URL}...")

        # Filter kwargs valid for the API (similar to OpenAI)
        valid_api_keys = {
            'temperature', 'max_tokens', 'top_p', 'frequency_penalty',
            'presence_penalty', 'stop', 'stream', 'model' # Ensure model override is passed
            # Add other OpenRouter specific keys if necessary
        }
        # Prepare kwargs for the API call, ensuring 'model' is included if passed in kwargs
        api_kwargs = {k: v for k, v in kwargs.items() if k in valid_api_keys}
        if 'model' not in api_kwargs: # Ensure the resolved model is passed if not overridden
             api_kwargs['model'] = model

        try:
            response = self.client.chat.completions.create(
                messages=messages,
                **api_kwargs # Pass model and other valid params
            )
            logger.debug("Received response from OpenRouter")

            if response.choices:
                content = response.choices[0].message.content
                return content.strip() if content else ""
            else:
                logger.warning("OpenRouter response did not contain any choices.")
                return ""

        except OpenAIError as e: # Catch OpenAIError
            logger.error(f"OpenRouter API call failed: {e}")
            # Add more specific error handling based on OpenRouter responses if needed
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenRouter API call: {e}")
            raise RuntimeError(f"Unexpected error during OpenRouter chat completion: {e}") from e