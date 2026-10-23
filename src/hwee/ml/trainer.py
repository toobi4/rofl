"""Supervised training loop: the student network learns the greeting from the cluster."""

from __future__ import annotations

from dataclasses import dataclass

from hwee.kernel.entropy import DeterministicEntropySource
from hwee.kernel.telemetry import TELEMETRY
from hwee.ml.autograd import Value
from hwee.ml.nn import MultiLayerPerceptron
from hwee.ml.optim import Adam

CODE_SCALE = 64.0
CODE_OFFSET = 64.0


def one_hot(index: int, size: int) -> list[float]:
    return [1.0 if i == index else 0.0 for i in range(size)]


@dataclass
class TrainingReport:
    epochs: int
    final_loss: float
    predictions: list[int]


class GreetingStudent:
    def __init__(self, length: int, hidden: int, entropy: DeterministicEntropySource) -> None:
        self.length = length
        self.model = MultiLayerPerceptron([length, hidden, hidden, 1], entropy)

    def predict(self, position: int) -> float:
        return self.model(one_hot(position, self.length))[0].data * CODE_SCALE + CODE_OFFSET

    def fit(self, targets: list[int], lr: float, max_epochs: int, tolerance: float) -> TrainingReport:
        optimizer = Adam(self.model.parameters(), lr=lr)
        scaled = [(t - CODE_OFFSET) / CODE_SCALE for t in targets]
        loss_value = float("inf")
        for epoch in range(1, max_epochs + 1):
            optimizer.zero_grad()
            loss = Value(0.0)
            for position, target in enumerate(scaled):
                prediction = self.model(one_hot(position, self.length))[0]
                loss = loss + (prediction - target) ** 2
            loss = loss * (1.0 / len(scaled))
            loss.backward()
            optimizer.step()
            loss_value = loss.data
            TELEMETRY.incr("ml.epochs")
            if epoch % 25 == 0:
                errors = [abs(self.predict(i) - t) for i, t in enumerate(targets)]
                TELEMETRY.log(f"    epoch {epoch}: loss={loss_value:.6f} max_err={max(errors):.3f}")
                if max(errors) < tolerance:
                    break
        predictions = [round(self.predict(i)) for i in range(self.length)]
        return TrainingReport(epoch, loss_value, predictions)
