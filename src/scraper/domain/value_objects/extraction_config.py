"""
ExtractionConfig - Responsabilidade única: Configuração de extração HTML
Elimina duplicação de parâmetros em múltiplas implementações
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ExtractionConfig:
    """Configuração parametrizada para extração HTML"""

    elements_to_remove: List[str] = field(
        default_factory=lambda: [
            "script",
            "style",
            "nav",
            "footer",
            "aside",
            "header",
            "form",
            "button",
            "input",
            "select",
            "textarea",
            "label",
            "iframe",
            "figure",
            "figcaption",
        ]
    )
    custom_elements_to_remove: List[str] = field(default_factory=list)
    use_chunked_processing: bool = True
    memory_limit_mb: int = 150
    parser: str = "html.parser"
    enable_fallback: bool = True
    chunk_size_threshold: int = 100 * 1024  # 100KB
    extra_noise_cleanup: bool = False

    def __post_init__(self):
        """Valida configuração após inicialização e combina elementos para remoção."""
        # Combina a lista padrão com a lista customizada
        if self.custom_elements_to_remove:
            # Evita duplicatas, embora seja improvável
            combined = set(self.elements_to_remove) | set(
                self.custom_elements_to_remove
            )
            self.elements_to_remove = list(combined)

        if self.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb must be positive")

        valid_parsers = ["html.parser", "lxml", "html5lib"]
        if self.parser not in valid_parsers:
            raise ValueError(
                f"Invalid parser: {self.parser}. Must be one of {valid_parsers}"
            )

        if self.chunk_size_threshold <= 0:
            raise ValueError("chunk_size_threshold must be positive")

    @classmethod
    def for_small_content(cls) -> "ExtractionConfig":
        """Configuração otimizada para conteúdo pequeno"""
        return cls(
            use_chunked_processing=False, memory_limit_mb=50, extra_noise_cleanup=False
        )

    @classmethod
    def for_large_content(cls) -> "ExtractionConfig":
        """Configuração otimizada para conteúdo grande"""
        return cls(
            use_chunked_processing=True,
            memory_limit_mb=200,
            chunk_size_threshold=50 * 1024,  # 50KB
            extra_noise_cleanup=True,
        )

    @classmethod
    def for_memory_constrained(cls) -> "ExtractionConfig":
        """Configuração para ambientes com pouca memória"""
        return cls(
            use_chunked_processing=True,
            memory_limit_mb=100,
            chunk_size_threshold=25 * 1024,  # 25KB
            extra_noise_cleanup=False,
        )
