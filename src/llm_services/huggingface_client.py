import os
import threading
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError 
from loguru import logger
from .base_client import BaseLLMService

class HuggingFaceService(BaseLLMService):
    """
    Singleton implementation for the Hugging Face Inference API client.

    Uses the huggingface_hub library's InferenceClient.
    Requires the HF_TOKEN environment variable or an api_key passed
    during the first instantiation.
    """

    _MODEL = "meta-llama/Llama-3.2-3B-Instruct"

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    logger.debug("Creating new HuggingFaceService instance")
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None, default_model: str = _MODEL):
        """
        Initializes the HuggingFaceService Singleton.

        Args:
            api_key (str, optional): Hugging Face API token (read/write). If None,
                                     attempts to read from HF_TOKEN environment variable.
                                     Defaults to None.
            default_model (str, optional): The default Hugging Face model ID to use.
                                           Defaults to "mistralai/Mistral-7B-Instruct-v0.1".

        Raises:
            ValueError: If no API token is provided or found in environment variables.
            ConnectionError: If the InferenceClient fails to initialize (e.g., invalid token).
        """
        if self._initialized:
            return

        with self._lock:
            if self._initialized: # Double-check after acquiring lock
                return

            logger.info("Initializing HuggingFaceService...")
            resolved_api_key = api_key or os.getenv('HF_TOKEN')

            if not resolved_api_key:
                logger.error("Hugging Face API token not provided and not found in HF_TOKEN environment variable.")
                raise ValueError("Hugging Face API token is required for initialization.")

            self.api_key = resolved_api_key
            self.default_model = default_model

            try:
                # Initialize the Hugging Face Inference Client
                # The token is passed directly here.
                self.client = InferenceClient(
                    model=self.default_model,
                    token=self.api_key
                    )
                logger.success(f"Hugging Face InferenceClient initialized successfully. Default model: {self.default_model}")
                self._initialized = True
            except HfHubHTTPError as e: # Catch specific HF HTTP errors
                logger.error(f"Failed to initialize Hugging Face InferenceClient (HTTP Error): {e}")
                # Check if it's an authentication error (status code 401)
                if e.response is not None and e.response.status_code == 401:
                     logger.error("Authentication failed. Please check your HF_TOKEN.")
                     raise ConnectionError(f"Authentication failed for Hugging Face: {e}") from e
                else:
                     raise ConnectionError(f"Failed to initialize Hugging Face Client (HTTP Error): {e}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Hugging Face client initialization: {e}")
                raise ConnectionError(f"Unexpected error initializing Hugging Face Client: {e}") from e

    @property
    def name(self) -> str:
        """Returns the service name."""
        return "huggingface"

    def chat_completion(self, prompt: str, **kwargs) -> str:
        """
        Generates text using the Hugging Face Inference API (typically via text-generation).

        Note: The InferenceClient might not have a dedicated "chat" endpoint like OpenAI.
        This method often uses the `text_generation` task. Ensure your prompt is formatted
        appropriately for the chosen model (e.g., using instruction templates if needed).

        Args:
            prompt (str): The input prompt. For instruction-tuned models, this should
                          often include the instruction and any context.
            **kwargs: Additional keyword arguments for the InferenceClient call, such as:
                - model (str): Override the default model ID.
                - max_new_tokens (int): Max tokens to generate (default: 256 in client).
                - temperature (float): Sampling temperature (default: 1.0).
                - top_p (float): Nucleus sampling parameter.
                - top_k (int): Top-k sampling parameter.
                - repetition_penalty (float): Penalty for repeating tokens.
                - stop_sequences (list[str]): Sequences to stop generation at.

        Returns:
            str: The generated text.

        Raises:
            RuntimeError: If the service is not initialized.
            HfHubHTTPError: If the API call fails (e.g., model not found, quota exceeded).
        """

        _MAX_TOKENS = 1500

        if not self._initialized or not self.client:
            raise RuntimeError("HuggingFaceService is not initialized.")

        model_id = kwargs.get("model", self.default_model)
        logger.debug(f"Sending prompt to Hugging Face model {model_id}...")

        # Prepare parameters for text_generation
        # Filter kwargs to pass only valid parameters to the InferenceClient method
        valid_api_keys = {
            'max_new_tokens', 'temperature', 'top_p', 'top_k',
            'repetition_penalty', 'stop_sequences', 'return_full_text'
            # Add others supported by InferenceClient.text_generation if needed
        }
        api_kwargs = {k: v for k, v in kwargs.items() if k in valid_api_keys}

        # Ensure return_full_text is False unless explicitly requested,
        # otherwise the prompt is included in the output.
        if 'return_full_text' not in api_kwargs:
            api_kwargs['return_full_text'] = False

        try:
            # Use the text_generation endpoint
            response = self.client.text_generation(
                prompt=prompt,
                max_new_tokens=_MAX_TOKENS,
                **api_kwargs
            )
            logger.debug("Received response from Hugging Face")

            # The response from text_generation (with return_full_text=False)
            # is typically the generated string directly.
            if isinstance(response, str):
                return response.strip()
            else:
                # Handle unexpected response format
                logger.warning(f"Unexpected response type from Hugging Face text_generation: {type(response)}. Response: {response}")
                return str(response).strip() # Attempt to convert to string

        except HfHubHTTPError as e:
            logger.error(f"Hugging Face API call failed for model {model_id}: {e}")
            # Provide more context if possible (e.g., model loading errors)
            if e.response is not None:
                 logger.error(f"HF Response Status: {e.response.status_code}, Content: {e.response.text}")
                 if "is currently loading" in e.response.text:
                      logger.warning(f"Model {model_id} might be loading. Consider retrying later.")
                 elif e.response.status_code == 404:
                      logger.error(f"Model {model_id} not found or invalid.")
            raise # Re-raise the specific HF error
        except Exception as e:
            logger.error(f"An unexpected error occurred during Hugging Face API call: {e}")
            raise RuntimeError(f"Unexpected error during Hugging Face text generation: {e}") from e
