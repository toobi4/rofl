"""Neurons, layers and multi-layer perceptrons."""

from __future__ import annotations

from hwee.kernel.entropy import DeterministicEntropySource
from hwee.ml.autograd import Value


class Neuron:
    def __init__(self, inputs: int, entropy: DeterministicEntropySource, linear: bool = False) -> None:
        scale = 1.0 / inputs ** 0.5
        self.weights = [Value((entropy.uniform() * 2 - 1) * scale) for _ in range(inputs)]
        self.bias = Value(0.0)
        self.linear = linear

    def __call__(self, x: list[Value | float]) -> Value:
        activation = self.bias
        for w, xi in zip(self.weights, x):
            if isinstance(xi, (int, float)) and xi == 0:
                continue  # sparse-aware kernel fusion
            activation = activation + w * xi
        return activation if self.linear else activation.tanh()

    def parameters(self) -> list[Value]:
        return [*self.weights, self.bias]


class Layer:
    def __init__(self, inputs: int, outputs: int, entropy: DeterministicEntropySource, linear: bool = False) -> None:
        self.neurons = [Neuron(inputs, entropy, linear) for _ in range(outputs)]

    def __call__(self, x: list[Value | float]) -> list[Value]:
        return [neuron(x) for neuron in self.neurons]

    def parameters(self) -> list[Value]:
        return [p for neuron in self.neurons for p in neuron.parameters()]


class MultiLayerPerceptron:
    def __init__(self, sizes: list[int], entropy: DeterministicEntropySource) -> None:
        self.layers = [Layer(sizes[i], sizes[i + 1], entropy, linear=(i == len(sizes) - 2))
                       for i in range(len(sizes) - 1)]

    def __call__(self, x: list[Value | float]) -> list[Value]:
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self) -> list[Value]:
        return [p for layer in self.layers for p in layer.parameters()]
