"""
Interface abstrata para Content Processing Service
Defines contract for content processing
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IContentProcessingService(ABC):
    """Interface abstrata para serviço de processamento de conteúdo"""

    @abstractmethod
    def process_content(
        self, content: str, config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Processa conteúdo de acordo com configurações

        Args:
            content: Conteúdo a ser processado
            config: Configurações opcionais de processamento

        Returns:
            Conteúdo processado
        """
        pass

    @abstractmethod
    def extract_text(self, html: str, **kwargs) -> str:
        """
        Extrai texto de HTML

        Args:
            html: Conteúdo HTML
            **kwargs: Parâmetros adicionais

        Returns:
            Texto extraído
        """
        pass
