"""
Interface abstrata para Scraping Configuration Service
Responsabilidade: Definir contrato para configuração de scraping
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class IScrapingConfigurationService(ABC):
    """Interface abstrata para serviço de configuração de scraping"""

    @abstractmethod
    def get_configuration(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtém configuração baseada em parâmetros

        Args:
            params: Parâmetros de entrada

        Returns:
            Configuração processada
        """
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Valida parâmetros de configuração

        Args:
            params: Parâmetros a serem validados

        Returns:
            True se válidos, False caso contrário
        """
        pass
