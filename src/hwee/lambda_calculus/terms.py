"""Term representations: named surface syntax and nameless de Bruijn core."""

from __future__ import annotations

from dataclasses import dataclass


# --- named surface syntax ---------------------------------------------------
@dataclass(frozen=True)
class NVar:
    name: str


@dataclass(frozen=True)
class NLam:
    param: str
    body: "Named"


@dataclass(frozen=True)
class NApp:
    fn: "Named"
    arg: "Named"


Named = NVar | NLam | NApp


# --- nameless core ------------------------------------------------------------
@dataclass(frozen=True)
class Var:
    index: int


@dataclass(frozen=True)
class Lam:
    body: "Term"


@dataclass(frozen=True)
class App:
    fn: "Term"
    arg: "Term"


Term = Var | Lam | App


def to_de_bruijn(term: Named, definitions: dict[str, Term], scope: tuple[str, ...] = ()) -> Term:
    if isinstance(term, NVar):
        if term.name in scope:
            return Var(scope.index(term.name))
        if term.name in definitions:
            return definitions[term.name]
        raise NameError(f"Unbound lambda variable {term.name!r}")
    if isinstance(term, NLam):
        return Lam(to_de_bruijn(term.body, definitions, (term.param, *scope)))
    return App(to_de_bruijn(term.fn, definitions, scope), to_de_bruijn(term.arg, definitions, scope))


def pretty(term: Term) -> str:
    if isinstance(term, Var):
        return str(term.index)
    if isinstance(term, Lam):
        return f"λ.{pretty(term.body)}"
    fn = pretty(term.fn) if not isinstance(term.fn, Lam) else f"({pretty(term.fn)})"
    arg = pretty(term.arg) if isinstance(term.arg, Var) else f"({pretty(term.arg)})"
    return f"{fn} {arg}"
