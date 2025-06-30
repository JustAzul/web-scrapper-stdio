"""
TDD Tests for T006: Padronizar Type Hints
Objetivo: Eliminar inconsistências entre list|None vs Optional[list] vs Optional[List]

FASE RED: Testes que falham primeiro - definindo padrão de type hints esperado
"""

from pathlib import Path
from typing import List


class TestTypeHintStandardization:
    """Testes para padronização de type hints - responsabilidade única de consistência"""

    def test_no_union_pipe_syntax_with_none(self):
        """Não deve usar sintaxe | com None (usar Optional ao invés)"""
        violations = self._find_union_pipe_with_none()

        # Deve estar vazio após padronização
        assert len(violations) == 0, f"Found Union | syntax with None: {violations}"

    def test_consistent_list_type_usage(self):
        """Deve usar List[T] consistentemente ao invés de list[T]"""
        violations = self._find_lowercase_list_usage()

        # Deve estar vazio após padronização
        assert len(violations) == 0, f"Found lowercase 'list' usage: {violations}"

    def test_no_optional_lowercase_list(self):
        """Não deve usar Optional[list] - deve ser Optional[List]"""
        violations = self._find_optional_lowercase_list()

        # Deve estar vazio após padronização
        assert len(violations) == 0, (
            f"Found Optional[list] instead of Optional[List]: {violations}"
        )

    def _find_union_pipe_with_none(self) -> List[str]:
        """Encontra uso de sintaxe | com None"""
        violations = []
        src_path = Path("src")

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                if " | None" in content:
                    violations.append(str(py_file))
            except Exception:
                continue

        return violations

    def _find_lowercase_list_usage(self) -> List[str]:
        """Encontra uso de list[T] ao invés de List[T]"""
        violations = []
        src_path = Path("src")

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "list[" in line and not line.strip().startswith("#"):
                        violations.append(f"{py_file}:{i + 1}")
            except Exception:
                continue

        return violations

    def _find_optional_lowercase_list(self) -> List[str]:
        """Encontra Optional[list] ao invés de Optional[List]"""
        violations = []
        src_path = Path("src")

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "Optional[list]" in content:
                    violations.append(str(py_file))
            except Exception:
                continue

        return violations


class TestBackwardCompatibility:
    """Testes para garantir compatibilidade após padronização"""

    def test_function_signatures_unchanged(self):
        """Assinaturas de função devem permanecer funcionalmente iguais"""
        from src.scraper import extract_clean_html

        # Deve funcionar com None
        result = extract_clean_html(
            html_content="<html><body><h1>Test</h1></body></html>",
            elements_to_remove=None,
            url="https://example.com",
        )

        assert isinstance(result, tuple)
        assert len(result) == 5
