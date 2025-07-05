from src.scraper.domain.exceptions import *

def test_custom_domain_exception_instantiation():
    class CustomDomainException(Exception):
        pass
    exc = CustomDomainException("Erro de domínio")
    assert isinstance(exc, Exception)
    assert str(exc) == "Erro de domínio"
