"""
Interface abstrata para Browser Factory
Responsabilidade: Definir contrato para criação e configuração de browsers
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IBrowserFactory(ABC):
    """Interface abstrata para factory de browsers"""

    @abstractmethod
    def create_browser(self, **kwargs) -> Any:
        """
        Cria uma instância de browser

        Args:
            **kwargs: Parâmetros de configuração do browser

        Returns:
            Instância do browser configurado
        """
        pass

    @abstractmethod
    def configure_browser(self, browser: Any, config: Optional[dict] = None) -> Any:
        """
        Configura um browser existente

        Args:
            browser: Instância do browser a ser configurado
            config: Configurações opcionais

        Returns:
            Browser configurado
        """
        pass
