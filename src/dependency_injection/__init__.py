"""
Módulo de Injeção de Dependência
Responsabilidade: Implementar padrão Dependency Injection para DIP compliance
"""

from .di_container import DIContainer
from .service_factory import ServiceFactory

# Global container instance
container = DIContainer()

__all__ = ["DIContainer", "ServiceFactory", "container"]
