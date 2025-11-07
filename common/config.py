"""
Configuration management for AI agent tutorials.
Handles environment variables and global settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # Project root

# Project paths
BASE_DIR = Path(__file__).parent.parent
COMMON_DIR = BASE_DIR / "common"
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)


class Config:
    """Configuration class for managing environment variables and settings."""
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Model Configuration
    MODEL_TYPE: str = os.getenv("MODEL_TYPE", "ollama")  # openai, anthropic, or ollama
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama3.1")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0"))
    
    # Ollama Configuration (for local models)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    
    # Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Backend Configuration
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not cls.OPENAI_API_KEY and cls.MODEL_TYPE == "openai":
            print("Warning: OPENAI_API_KEY not set but MODEL_TYPE is 'openai'.")
            print("Set it in .env file or use a different MODEL_TYPE.")
            return False
        if not cls.ANTHROPIC_API_KEY and cls.MODEL_TYPE == "anthropic":
            print("Warning: ANTHROPIC_API_KEY not set but MODEL_TYPE is 'anthropic'.")
            print("Set it in .env file or use a different MODEL_TYPE.")
            return False
        return True
    
    @classmethod
    def get_model_config(cls, model_type: str = None) -> dict:
        """
        Get model configuration based on type.
        
        Args:
            model_type: Type of model ("openai", "anthropic", or "ollama")
                       If None, uses MODEL_TYPE from config
            
        Returns:
            Dictionary with model configuration
        """
        model_type = model_type or cls.MODEL_TYPE
        
        if model_type == "openai":
            return {
                "model": cls.DEFAULT_MODEL,
                "temperature": cls.DEFAULT_TEMPERATURE,
                "api_key": cls.OPENAI_API_KEY
            }
        elif model_type == "anthropic":
            return {
                "model": "claude-3-sonnet-20240229",
                "temperature": cls.DEFAULT_TEMPERATURE,
                "api_key": cls.ANTHROPIC_API_KEY
            }
        elif model_type == "ollama":
            return {
                "model": cls.OLLAMA_MODEL,
                "base_url": cls.OLLAMA_BASE_URL,
                "temperature": cls.DEFAULT_TEMPERATURE
            }
        else:
            raise ValueError(f"Unknown model type: {model_type}")


# Global config instance
config = Config()
