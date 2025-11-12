"""
Configuration management for AI agent tutorials.
Handles environment variables and global settings.
"""

import os
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # Project root

# Project paths
BASE_DIR = Path(__file__).parent.parent
COMMON_DIR = BASE_DIR / "common"
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)


def _parse_model_config(env_var: str, default: str = "ollama:llama3.1") -> tuple[str, str]:
    """
    Parse model configuration from environment variable.
    
    Args:
        env_var: Environment variable name
        default: Default value in "provider:model_name" format
        
    Returns:
        Tuple of (model_type, model_name)
        
    Raises:
        ValueError: If the format is invalid
    """
    model_str = os.getenv(env_var, default)
    
    if ":" not in model_str:
        raise ValueError(
            f"Invalid model configuration for {env_var}: '{model_str}'. "
            f"Expected format: 'provider:model_name' (e.g., 'openai:gpt-4o-mini')"
        )
    
    parts = model_str.split(":", 1)
    model_type = parts[0].strip()
    model_name = parts[1].strip()
    
    valid_types = ["openai", "anthropic", "ollama"]
    if model_type not in valid_types:
        raise ValueError(
            f"Invalid model type '{model_type}' in {env_var}. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    return model_type, model_name


# Parse model configurations
_default_type, _default_name = _parse_model_config("DEFAULT_MODEL", "ollama:llama3.1")
_planner_type, _planner_name = _parse_model_config("PLANNER_MODEL", "ollama:llama3.1")
_solver_type, _solver_name = _parse_model_config("SOLVER_MODEL", "ollama:llama3.1")


class Config:
    """Configuration class for managing environment variables and settings."""
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Model Configuration
    # Models are configured as "provider:model_name" (e.g., "openai:gpt-4o-mini")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0"))
    
    # Assign parsed configurations
    DEFAULT_MODEL_TYPE: str = _default_type
    DEFAULT_MODEL_NAME: str = _default_name
    PLANNER_MODEL_TYPE: str = _planner_type
    PLANNER_MODEL_NAME: str = _planner_name
    SOLVER_MODEL_TYPE: str = _solver_type
    SOLVER_MODEL_NAME: str = _solver_name
    
    # Ollama Configuration (for local models)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    
    # Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_CHECKPOINTING: bool = os.getenv("ENABLE_CHECKPOINTING", "false").lower() == "true"
    
    # Stage Configuration
    # Supports: 1, 2, 3.1 (ReWOO), 3.2 (Reflection), 3.3 (Plan-Execute)
    STAGE: Union[int, float] = (
        float(os.getenv("STAGE", "1")) if '.' in os.getenv("STAGE", "1") 
        else int(os.getenv("STAGE", "1"))
    )
    
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
        # Check DEFAULT_MODEL configuration
        if not cls.OPENAI_API_KEY and cls.DEFAULT_MODEL_TYPE == "openai":
            print("Warning: OPENAI_API_KEY not set but DEFAULT_MODEL uses 'openai'.")
            print("Set it in .env file or use a different model provider.")
            return False
        if not cls.ANTHROPIC_API_KEY and cls.DEFAULT_MODEL_TYPE == "anthropic":
            print("Warning: ANTHROPIC_API_KEY not set but DEFAULT_MODEL uses 'anthropic'.")
            print("Set it in .env file or use a different model provider.")
            return False
        
        # Check PLANNER_MODEL configuration
        if not cls.OPENAI_API_KEY and cls.PLANNER_MODEL_TYPE == "openai":
            print("Warning: OPENAI_API_KEY not set but PLANNER_MODEL uses 'openai'.")
            print("Set it in .env file or use a different model provider.")
            return False
        if not cls.ANTHROPIC_API_KEY and cls.PLANNER_MODEL_TYPE == "anthropic":
            print("Warning: ANTHROPIC_API_KEY not set but PLANNER_MODEL uses 'anthropic'.")
            print("Set it in .env file or use a different model provider.")
            return False
        
        # Check SOLVER_MODEL configuration
        if not cls.OPENAI_API_KEY and cls.SOLVER_MODEL_TYPE == "openai":
            print("Warning: OPENAI_API_KEY not set but SOLVER_MODEL uses 'openai'.")
            print("Set it in .env file or use a different model provider.")
            return False
        if not cls.ANTHROPIC_API_KEY and cls.SOLVER_MODEL_TYPE == "anthropic":
            print("Warning: ANTHROPIC_API_KEY not set but SOLVER_MODEL uses 'anthropic'.")
            print("Set it in .env file or use a different model provider.")
            return False
        
        return True


# Global config instance
config = Config()
