"""Модуль для работы с конфигурацией Talkie."""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Environment(BaseModel):
    """Модель для описания окружения."""
    
    name: str = Field(..., description="Имя окружения")
    base_url: Optional[str] = Field(None, description="Базовый URL для запросов")
    default_headers: Dict[str, str] = Field(default_factory=dict, description="Заголовки по умолчанию")
    auth: Optional[Dict[str, str]] = Field(None, description="Данные аутентификации")


class Config(BaseModel):
    """Talkie configuration model."""
    
    default_headers: Dict[str, str] = Field(
        default_factory=lambda: {"User-Agent": "Talkie/0.1.0"},
        description="Default headers"
    )
    environments: Dict[str, Environment] = Field(
        default_factory=dict,
        description="Configured environments"
    )
    active_environment: Optional[str] = Field(
        None, description="Current active environment"
    )
    
    @classmethod
    def load_default(cls) -> "Config":
        """Load default configuration.
        
        Returns:
            Config: configuration object
        """
        config_path = cls._get_config_path()
        
        if not config_path.exists():
            # Create default configuration
            return cls._create_default_config()
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            return cls(**config_data)
        except Exception:
            # Return default configuration in case of error
            return cls()
    
    def save(self) -> None:
        """Save configuration to file."""
        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(self.json(indent=2, ensure_ascii=False))
    
    def get_active_environment(self) -> Optional[Environment]:
        """Получить активное окружение.
        
        Returns:
            Optional[Environment]: объект активного окружения или None
        """
        if not self.active_environment:
            return None
        
        return self.environments.get(self.active_environment)
    
    @staticmethod
    def _get_config_path() -> Path:
        """Получить путь к файлу конфигурации.
        
        Returns:
            Path: путь к файлу конфигурации
        """
        # Определяем путь к конфигурационному файлу
        config_dir = os.environ.get(
            "TALKIE_CONFIG_DIR",
            os.path.expanduser("~/.talkie")
        )
        
        return Path(config_dir) / "config.json"
    
    @classmethod
    def _create_default_config(cls) -> "Config":
        """Создать конфигурацию по умолчанию.
        
        Returns:
            Config: конфигурация по умолчанию
        """
        config = cls()
        config.save()
        return config 