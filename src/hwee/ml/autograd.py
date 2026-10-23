"""Scalar reverse-mode autodiff. One Python object per floating point number."""

from __future__ import annotations

import math


class Value:
    __slots__ = ("data", "grad", "_parents", "_backward")

    def __init__(self, data: float, parents: tuple["Value", ...] = ()) -> None:
        self.data = float(data)
        self.grad = 0.0
        self._parents = parents
        self._backward = None

    @staticmethod
    def lift(other: "Value | float") -> "Value":
        return other if isinstance(other, Value) else Value(other)

    def __add__(self, other: "Value | float") -> "Value":
        other = Value.lift(other)
        out = Value(self.data + other.data, (self, other))

        def backward() -> None:
            self.grad += out.grad
            other.grad += out.grad
        out._backward = backward
        return out

    __radd__ = __add__

    def __mul__(self, other: "Value | float") -> "Value":
        other = Value.lift(other)
        out = Value(self.data * other.data, (self, other))

        def backward() -> None:
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = backward
        return out

    __rmul__ = __mul__

    def __neg__(self) -> "Value":
        return self * -1.0

    def __sub__(self, other: "Value | float") -> "Value":
        return self + (-Value.lift(other))

    def __rsub__(self, other: float) -> "Value":
        return Value.lift(other) - self

    def __pow__(self, exponent: float) -> "Value":
        out = Value(self.data ** exponent, (self,))

        def backward() -> None:
            self.grad += exponent * self.data ** (exponent - 1) * out.grad
        out._backward = backward
        return out

    def tanh(self) -> "Value":
        t = math.tanh(self.data)
        out = Value(t, (self,))

        def backward() -> None:
            self.grad += (1.0 - t * t) * out.grad
        out._backward = backward
        return out

    def backward(self) -> None:
        order: list[Value] = []
        visited: set[int] = set()
        stack: list[tuple[Value, bool]] = [(self, False)]
        while stack:
            node, expanded = stack.pop()
            if expanded:
                order.append(node)
                continue
            if id(node) in visited:
                continue
            visited.add(id(node))
            stack.append((node, True))
            for parent in node._parents:
                if id(parent) not in visited:
                    stack.append((parent, False))
        self.grad = 1.0
        for node in reversed(order):
            if node._backward is not None:
                node._backward()
