"""Adaptive Moment Estimation, implemented one scalar at a time."""

from __future__ import annotations

from hwee.ml.autograd import Value


class Adam:
    def __init__(self, parameters: list[Value], lr: float = 0.01, betas=(0.9, 0.999), eps: float = 1e-8) -> None:
        self.parameters = parameters
        self.lr = lr
        self.beta1, self.beta2 = betas
        self.eps = eps
        self.m = [0.0] * len(parameters)
        self.v = [0.0] * len(parameters)
        self.t = 0

    def zero_grad(self) -> None:
        for p in self.parameters:
            p.grad = 0.0

    def step(self) -> None:
        self.t += 1
        c1 = 1 - self.beta1 ** self.t
        c2 = 1 - self.beta2 ** self.t
        for i, p in enumerate(self.parameters):
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * p.grad * p.grad
            p.data -= self.lr * (self.m[i] / c1) / ((self.v[i] / c2) ** 0.5 + self.eps)
