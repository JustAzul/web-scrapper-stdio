"""
OutputFormatter - Responsabilidade única: Formatação de conteúdo para diferentes outputs
Parte da refatoração T001 - Quebrar extract_text_from_url seguindo SRP
"""

from typing import Optional

from bs4 import BeautifulSoup

from src.enums import OutputFormat
from src.logger import get_logger
from src.output_format_handler import (
    TRUNCATION_NOTICE,
    to_markdown,
    to_text,
)

logger = get_logger(__name__)


class OutputFormatter:
    """
    Formata conteúdo para diferentes outputs
    seguindo Single Responsibility Principle
    """

    def __init__(self) -> None:
        self.logger = logger

    def format(
        self,
        content: str,
        output_format: OutputFormat,
        soup: Optional[BeautifulSoup] = None,
    ) -> str:
        """
        Formata conteúdo para o formato especificado

        Args:
            content: Conteúdo para formatar (HTML limpo ou texto)
            output_format: Formato desejado
            soup: BeautifulSoup object opcional para formatação TEXT

        Returns:
            Conteúdo formatado
        """
        try:
            if output_format == OutputFormat.MARKDOWN:
                return self.format_markdown(content)
            elif output_format == OutputFormat.TEXT:
                return self.format_text(soup)
            elif output_format == OutputFormat.HTML:
                return self.format_html(content)
            else:  # Fallback for any unhandled format
                return self.format_markdown(content)

        except Exception as e:
            self.logger.error(f"Erro formatando conteúdo: {e}")
            return content  # Fallback para conteúdo original

    def format_markdown(self, html_content: str) -> str:
        """
        Formata HTML para Markdown

        Args:
            html_content: Conteúdo HTML limpo

        Returns:
            Conteúdo em formato Markdown
        """
        try:
            result = to_markdown(html_content)
            return str(result) if result is not None else html_content
        except Exception as e:
            self.logger.error(f"Erro convertendo para Markdown: {e}")
            return html_content

    def format_text(self, soup: Optional[BeautifulSoup]) -> str:
        """
        Formata para texto plano usando BeautifulSoup

        Args:
            soup: Objeto BeautifulSoup

        Returns:
            Conteúdo em texto plano
        """
        try:
            if soup is None:
                return ""
            result = to_text(soup=soup)
            return str(result) if result is not None else ""
        except Exception as e:
            self.logger.error(f"Erro convertendo para texto: {e}")
            return ""

    def format_html(self, clean_html: str) -> str:
        """
        Formata para HTML (retorna body ou HTML limpo)

        Args:
            clean_html: HTML já limpo

        Returns:
            Conteúdo HTML formatado
        """
        try:
            return clean_html
        except Exception as e:
            self.logger.error(f"Erro formatando HTML: {e}")
            return clean_html

    def truncate(self, content: str, max_length: int) -> str:
        """Truncates content to a maximum length, including notice."""
        if max_length and len(content) > max_length:
            notice_length = len(TRUNCATION_NOTICE)
            # Ensure we have space for the notice
            if max_length > notice_length:
                return content[: max_length - notice_length] + TRUNCATION_NOTICE
            else:
                # If max_length is smaller than notice, just truncate to max_length
                return content[:max_length]
        return content

    def format_and_truncate(
        self,
        content: str,
        output_format: OutputFormat,
        max_length: Optional[int] = None,
        soup: Optional[BeautifulSoup] = None,
    ) -> str:
        """
        Formata e trunca conteúdo em uma operação

        Args:
            content: Conteúdo para formatar
            output_format: Formato desejado
            max_length: Comprimento máximo opcional
            soup: BeautifulSoup object opcional

        Returns:
            Conteúdo formatado e truncado
        """
        formatted = self.format(content, output_format, soup)
        return self.truncate(formatted, max_length)
