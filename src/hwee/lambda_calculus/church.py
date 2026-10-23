"""Church numeral decoding: counting applications of the successor variable."""

from __future__ import annotations

from hwee.kernel.errors import OracleError
from hwee.lambda_calculus.terms import App, Lam, Term, Var


def decode_numeral(term: Term) -> int:
    if not (isinstance(term, Lam) and isinstance(term.body, Lam)):
        raise OracleError("Normal form is not a Church numeral (missing binders)")
    body = term.body.body
    count = 0
    while isinstance(body, App):
        if body.fn != Var(1):
            raise OracleError("Normal form is not a Church numeral (foreign head)")
        body = body.arg
        count += 1
    if body != Var(0):
        raise OracleError("Normal form is not a Church numeral (bad tail)")
    return count
