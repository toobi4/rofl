"""Inversion-of-Control container with constructor autowiring."""

from __future__ import annotations

import enum
import inspect
import typing
from dataclasses import dataclass
from typing import Any, Callable

from hwee.kernel.errors import DependencyResolutionError


class Lifetime(enum.Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"


@dataclass
class Registration:
    interface: type
    implementation: type | None
    factory: Callable[["Container"], Any] | None
    lifetime: Lifetime
    instance: Any = None
    has_instance: bool = False


class Container:
    def __init__(self) -> None:
        self._registrations: dict[type, Registration] = {}
        self._resolving: list[type] = []

    def register(self, interface: type, implementation: type | None = None, *,
                 factory: Callable[["Container"], Any] | None = None,
                 instance: Any = None, lifetime: Lifetime = Lifetime.SINGLETON) -> "Container":
        registration = Registration(interface, implementation or (None if factory or instance is not None else interface),
                                    factory, lifetime)
        if instance is not None:
            registration.instance = instance
            registration.has_instance = True
        self._registrations[interface] = registration
        return self

    def is_registered(self, interface: type) -> bool:
        return interface in self._registrations

    def resolve(self, interface: type) -> Any:
        registration = self._registrations.get(interface)
        if registration is None:
            raise DependencyResolutionError(f"No registration for {interface!r}")
        if registration.has_instance:
            return registration.instance
        if interface in self._resolving:
            chain = " -> ".join(t.__name__ for t in [*self._resolving, interface])
            raise DependencyResolutionError(f"Circular dependency: {chain}")
        self._resolving.append(interface)
        try:
            if registration.factory is not None:
                value = registration.factory(self)
            else:
                value = self.construct(registration.implementation)
        finally:
            self._resolving.pop()
        if registration.lifetime is Lifetime.SINGLETON:
            registration.instance = value
            registration.has_instance = True
        return value

    def construct(self, cls: type, **overrides: Any) -> Any:
        """Instantiate ``cls`` resolving every annotated constructor parameter."""
        signature = inspect.signature(cls.__init__)
        try:
            hints = typing.get_type_hints(cls.__init__)
        except Exception as exc:  # pragma: no cover - defensive
            raise DependencyResolutionError(f"Cannot introspect {cls!r}: {exc}") from exc
        kwargs: dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            if name == "self" or parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
                continue
            if name in overrides:
                kwargs[name] = overrides[name]
                continue
            hint = hints.get(name)
            if hint is not None and self.is_registered(hint):
                kwargs[name] = self.resolve(hint)
            elif parameter.default is not parameter.empty:
                continue
            else:
                raise DependencyResolutionError(
                    f"Cannot autowire parameter {name!r} of {cls.__name__} (hint={hint!r})")
        return cls(**kwargs)
