"""
Configuration Management for Gemini Podcast Generator

Handles configuration loading, validation, and secrets management for the 
podcast generator module. Provides a central place to manage API keys,
project settings, and generation parameters.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("podcast_config")


@dataclass
class GeminiConfig:
    """Configuration for Gemini API access."""
    project_id: str
    location: str = "us-central1"
    model_name: str = "gemini-1.5-pro"
    service_account_path: Optional[str] = None
    temperature: float = 0.7
    max_output_tokens: int = 8192


class ConfigManager:
    """
    Manages configuration for the podcast generator application.
    Handles loading from environment variables or config files.
    """
    
    # Default config file paths
    DEFAULT_CONFIG_PATHS = [
        "./config.json",
        "./config/config.json",
        os.path.expanduser("~/.config/podcast_generator/config.json"),
    ]
    
    # Environment variable prefixes
    ENV_PREFIX = "PODCAST_GEN_"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to a JSON configuration file
        """
        self.config_path = config_path
        self.config = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from files and environment variables."""
        # First, try to load from specified config file
        if self.config_path and os.path.exists(self.config_path):
            self._load_from_file(self.config_path)
            return
        
        # If no specified file, try default locations
        for path in self.DEFAULT_CONFIG_PATHS:
            if os.path.exists(path):
                self._load_from_file(path)
                return
        
        # If no config file found, load from environment variables
        self._load_from_env()
        
        # Validate that we have the minimum required config
        self._validate_config()
    
    def _load_from_file(self, file_path: str) -> None:
        """Load configuration from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {file_path}")
        except Exception as e:
            logger.error(f"Error loading config from {file_path}: {e}")
            # Fall back to environment variables
            self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Map of environment variables to config keys
        env_mapping = {
            f"{self.ENV_PREFIX}PROJECT_ID": "project_id",
            f"{self.ENV_PREFIX}LOCATION": "location",
            f"{self.ENV_PREFIX}MODEL_NAME": "model_name",
            f"{self.ENV_PREFIX}SERVICE_ACCOUNT_PATH": "service_account_path",
            f"{self.ENV_PREFIX}TEMPERATURE": "temperature",
            f"{self.ENV_PREFIX}MAX_OUTPUT_TOKENS": "max_output_tokens",
        }
        
        # Extract values from environment
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Convert types appropriately
                if config_key in ["temperature"]:
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"Invalid float value for {env_var}: {value}")
                        continue
                
                elif config_key in ["max_output_tokens"]:
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid int value for {env_var}: {value}")
                        continue
                
                self.config[config_key] = value
        
        logger.info("Loaded configuration from environment variables")
    
    def _validate_config(self) -> None:
        """Validate that the configuration has all required fields."""
        required_fields = ["project_id"]
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required configuration: {field}")
    
    def get_gemini_config(self) -> GeminiConfig:
        """
        Get Gemini API configuration.
        
        Returns:
            GeminiConfig object with Gemini API settings
        """
        return GeminiConfig(
            project_id=self.config.get("project_id"),
            location=self.config.get("location", "us-central1"),
            model_name=self.config.get("model_name", "gemini-1.5-pro"),
            service_account_path=self.config.get("service_account_path"),
            temperature=self.config.get("temperature", 0.7),
            max_output_tokens=self.config.get("max_output_tokens", 8192)
        )
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value in memory.
        
        Args:
            key: Configuration key to set
            value: Value to assign
        """
        self.config[key] = value
    
    def save_config(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to a file.
        
        Args:
            file_path: Optional file path to save to (otherwise uses the loaded path)
        """
        save_path = file_path or self.config_path
        
        if not save_path:
            raise ValueError("No file path specified for saving configuration")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # Write config to file
            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved configuration to {save_path}")
        
        except Exception as e:
            logger.error(f"Error saving configuration to {save_path}: {e}")
            raise


def create_default_config(output_path: str) -> None:
    """
    Create a default configuration file.
    
    Args:
        output_path: Path to save the default configuration
    """
    default_config = {
        "project_id": "your-project-id",
        "location": "us-central1",
        "model_name": "gemini-1.5-pro",
        "service_account_path": "/path/to/service-account.json",
        "temperature": 0.7,
        "max_output_tokens": 8192,
    }
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Write default config
        with open(output_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default configuration at {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating default configuration: {e}")
        raise


if __name__ == "__main__":
    # Example: Create a default configuration file
    create_default_config("./config.json")