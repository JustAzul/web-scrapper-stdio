"""
FallbackHandler - Responsabilidade única: Gerenciamento de fallback
Parte da refatoração T002 - Quebrar ChunkedHTMLProcessor seguindo SRP
"""

from typing import Callable, TypeVar

from src.logger import Logger

logger = Logger(__name__)

T = TypeVar("T")


class FallbackHandler:
    """Gerencia fallback para operações que podem falhar seguindo SRP"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = logger

    def execute_with_fallback(
        self, primary_operation: Callable[[], T], fallback_operation: Callable[[], T]
    ) -> T:
        """
        Executa operação principal com fallback automático

        Args:
            primary_operation: Operação principal a tentar primeiro
            fallback_operation: Operação de fallback se a principal falhar

        Returns:
            Resultado da operação principal ou fallback

        Raises:
            Exception: Se fallback estiver desabilitado e operação principal falhar
        """
        try:
            return primary_operation()
        except Exception as e:
            self.logger.warning(f"Primary operation failed: {e}")

            if not self.enabled:
                # Se fallback desabilitado, propaga exceção original
                raise

            try:
                self.logger.info("Attempting fallback operation")
                return fallback_operation()
            except Exception as fallback_error:
                self.logger.error(f"Fallback operation also failed: {fallback_error}")
                # Propaga erro do fallback se também falhar
                raise fallback_error

    def execute_with_fallback_async(
        self, primary_operation: Callable[[], T], fallback_operation: Callable[[], T]
    ) -> T:
        """
        Versão assíncrona do execute_with_fallback

        Args:
            primary_operation: Operação principal assíncrona
            fallback_operation: Operação de fallback assíncrona

        Returns:
            Resultado da operação principal ou fallback
        """
        # Para simplicidade, usa a mesma lógica síncrona
        # Em implementação real, seria async/await
        return self.execute_with_fallback(primary_operation, fallback_operation)

    def is_enabled(self) -> bool:
        """
        Verifica se fallback está habilitado

        Returns:
            True se fallback está habilitado
        """
        return self.enabled

    def enable(self) -> None:
        """Habilita fallback"""
        self.enabled = True
        self.logger.debug("Fallback handler enabled")

    def disable(self) -> None:
        """Desabilita fallback"""
        self.enabled = False
        self.logger.debug("Fallback handler disabled")
