"""
Model factory for creating LLM instances across different providers.
Supports OpenAI, Anthropic, and Ollama with consistent interface.
"""

from typing import Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

from common.config import config
from common.logging_config import get_logger

logger = get_logger(__name__)

ModelType = Literal["openai", "anthropic", "ollama"]


class ModelFactory:
    """
    Factory for creating LLM instances with consistent configuration.
    
    Supports multiple providers:
    - OpenAI (GPT-4, GPT-3.5, etc.)
    - Anthropic (Claude models)
    - Ollama (local models)
    """
    
    @staticmethod
    def create_model(
        model_type: ModelType,
        model_name: str,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """
        Create an LLM instance based on the specified type.
        
        Args:
            model_type: Type of model ("openai", "anthropic", or "ollama")
            model_name: Specific model name
            temperature: Temperature for generation (0-1). If None, uses DEFAULT_TEMPERATURE from config
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured chat model instance
            
        Raises:
            ValueError: If model_type is not supported or required config is missing
            
        Examples:
            >>> # OpenAI model
            >>> model = ModelFactory.create_model("openai", "gpt-4o-mini")
            
            >>> # Anthropic model
            >>> model = ModelFactory.create_model("anthropic", "claude-3-sonnet-20240229")
            
            >>> # Local Ollama model
            >>> model = ModelFactory.create_model("ollama", "llama2")
        """
        # Use config default temperature if not explicitly provided
        temperature = temperature if temperature is not None else config.DEFAULT_TEMPERATURE
        
        logger.info(f"Creating model - type: {model_type}, name: {model_name}, temp: {temperature}")
        
        if model_type == "openai":
            return ModelFactory._create_openai_model(model_name, temperature, **kwargs)
        
        elif model_type == "anthropic":
            return ModelFactory._create_anthropic_model(model_name, temperature, **kwargs)
        
        elif model_type == "ollama":
            return ModelFactory._create_ollama_model(model_name, temperature, **kwargs)
        
        else:
            raise ValueError(
                f"Unsupported model_type: {model_type}. "
                f"Must be one of: 'openai', 'anthropic', 'ollama'"
            )
    
    @staticmethod
    def _create_openai_model(
        model_name: str,
        temperature: float,
        **kwargs
    ) -> ChatOpenAI:
        """
        Create OpenAI chat model.
        
        Args:
            model_name: Model name (e.g., "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo")
            temperature: Temperature for generation
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            ChatOpenAI instance
        """
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found in environment. "
                "Set it in .env file or use a different model_type."
            )
        
        model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=config.OPENAI_API_KEY,
            **kwargs
        )
        
        logger.info(f"OpenAI model created - model: {model_name}, temperature: {temperature}")
        return model
    
    @staticmethod
    def _create_anthropic_model(
        model_name: str,
        temperature: float,
        **kwargs
    ) -> ChatAnthropic:
        """
        Create Anthropic chat model.
        
        Args:
            model_name: Model name (e.g., "claude-3-sonnet-20240229", "claude-3-opus-20240229")
            temperature: Temperature for generation
            **kwargs: Additional Anthropic-specific parameters
            
        Returns:
            ChatAnthropic instance
        """
        if not config.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Set it in .env file or use a different model_type."
            )
        
        model = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            api_key=config.ANTHROPIC_API_KEY,
            **kwargs
        )
        
        logger.info(f"Anthropic model created - model: {model_name}, temperature: {temperature}")
        return model
    
    @staticmethod
    def _create_ollama_model(
        model_name: str,
        temperature: float,
        **kwargs
    ) -> ChatOllama:
        """
        Create Ollama chat model (local).
        
        Args:
            model_name: Model name (e.g., "llama2", "mistral", "codellama")
            temperature: Temperature for generation
            **kwargs: Additional Ollama-specific parameters
            
        Returns:
            ChatOllama instance
        """
        base_url = kwargs.pop("base_url", config.OLLAMA_BASE_URL)
        
        model = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )
        
        logger.info(f"Ollama model created - model: {model_name}, base_url: {base_url}, temperature: {temperature}")
        return model
