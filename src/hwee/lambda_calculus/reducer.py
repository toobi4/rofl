"""Leftmost-outermost (normal order) beta reduction to normal form."""

from __future__ import annotations

from hwee.kernel.errors import ReductionLimitExceeded
from hwee.kernel.telemetry import TELEMETRY
from hwee.lambda_calculus.terms import App, Lam, Term, Var


def shift(term: Term, delta: int, cutoff: int = 0) -> Term:
    if isinstance(term, Var):
        return Var(term.index + delta) if term.index >= cutoff else term
    if isinstance(term, Lam):
        return Lam(shift(term.body, delta, cutoff + 1))
    return App(shift(term.fn, delta, cutoff), shift(term.arg, delta, cutoff))


def substitute(term: Term, index: int, replacement: Term) -> Term:
    if isinstance(term, Var):
        return replacement if term.index == index else term
    if isinstance(term, Lam):
        return Lam(substitute(term.body, index + 1, shift(replacement, 1)))
    return App(substitute(term.fn, index, replacement), substitute(term.arg, index, replacement))


def beta(body: Term, argument: Term) -> Term:
    return shift(substitute(body, 0, shift(argument, 1)), -1)


def step(term: Term) -> Term | None:
    if isinstance(term, App):
        if isinstance(term.fn, Lam):
            return beta(term.fn.body, term.arg)
        reduced = step(term.fn)
        if reduced is not None:
            return App(reduced, term.arg)
        reduced = step(term.arg)
        if reduced is not None:
            return App(term.fn, reduced)
        return None
    if isinstance(term, Lam):
        reduced = step(term.body)
        return Lam(reduced) if reduced is not None else None
    return None


def normalize(term: Term, limit: int = 1_000_000) -> tuple[Term, int]:
    steps = 0
    while True:
        reduced = step(term)
        if reduced is None:
            TELEMETRY.incr("lambda.beta_reductions", steps)
            return term, steps
        term = reduced
        steps += 1
        if steps > limit:
            raise ReductionLimitExceeded(f"No normal form within {limit} beta steps")
