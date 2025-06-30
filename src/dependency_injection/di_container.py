"""
Dependency Injection Container
Responsabilidade única: Gerenciar registro e resolução de dependências
"""

import inspect
from typing import Any, Callable, Dict, Type, TypeVar, Union

T = TypeVar("T")


class DIContainer:
    """Container de Dependency Injection para gerenciar dependências"""

    def __init__(self):
        self._services: Dict[Union[str, Type], Callable[[], Any]] = {}
        self._singletons: Dict[Union[str, Type], Any] = {}
        self._singleton_factories: Dict[Union[str, Type], Callable[[], Any]] = {}

    def register(
        self, interface: Union[str, Type[T]], factory: Callable[[], T]
    ) -> None:
        """
        Registra uma dependência transiente

        Args:
            interface: Interface ou chave de identificação
            factory: Factory function para criar a instância
        """
        self._services[interface] = factory

    def register_singleton(
        self, interface: Union[str, Type[T]], factory: Callable[[], T]
    ) -> None:
        """
        Registra uma dependência singleton

        Args:
            interface: Interface ou chave de identificação
            factory: Factory function para criar a instância (chamada apenas uma vez)
        """
        self._singleton_factories[interface] = factory

    def resolve(self, interface: Union[str, Type[T]]) -> T:
        """
        Resolve uma dependência

        Args:
            interface: Interface ou chave a ser resolvida

        Returns:
            Instância da dependência

        Raises:
            KeyError: Se a dependência não estiver registrada
        """
        # Verifica se é singleton já instanciado
        if interface in self._singletons:
            return self._singletons[interface]

        # Verifica se é singleton a ser instanciado
        if interface in self._singleton_factories:
            instance = self._singleton_factories[interface]()
            self._singletons[interface] = instance
            return instance

        # Verifica se é serviço transiente
        if interface in self._services:
            return self._services[interface]()

        raise KeyError(f"Service not registered: {interface}")

    def resolve_with_dependencies(self, target_class: Type[T]) -> T:
        """
        Resolve uma classe injetando suas dependências automaticamente

        Args:
            target_class: Classe a ser instanciada com DI

        Returns:
            Instância da classe com dependências injetadas
        """
        # Obtém signature do construtor
        signature = inspect.signature(target_class.__init__)
        kwargs = {}

        # Resolve cada parâmetro do construtor
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            # Tenta resolver pela annotation do tipo
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.resolve(param.annotation)
                except KeyError:
                    # Se não conseguir resolver pela annotation, tenta pelo nome
                    try:
                        kwargs[param_name] = self.resolve(param_name)
                    except KeyError:
                        if param.default == inspect.Parameter.empty:
                            raise KeyError(f"Cannot resolve dependency: {param_name}")

        return target_class(**kwargs)

    def is_registered(self, interface: Union[str, Type]) -> bool:
        """
        Verifica se uma interface está registrada

        Args:
            interface: Interface a ser verificada

        Returns:
            True se estiver registrada, False caso contrário
        """
        return (
            interface in self._services
            or interface in self._singleton_factories
            or interface in self._singletons
        )
