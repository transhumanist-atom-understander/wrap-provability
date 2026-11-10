"""The R⁻ decider's verdicts on sentences of R⁻, Guaspari and Solovay's logic of witness
comparisons, and the check of them by the semantics of R⁻.

There is no verifier of R⁻ tableaux yet, so the sentences below come with their verdicts, which
are the papers' or follow from the semantics, and `test_semantics` has `rminus_models` decide
each of them again, by brute force, from the models of R⁻ alone. A sentence can be added to
`SENTENCES` without knowing its verdict.
"""

import pytest

from rminus_models import sentence, theorem
from test_gl import NON_THEOREMS as GL_NON_THEOREMS
from test_gl import THEOREMS as GL_THEOREMS

THEOREMS = [
    # the order axioms of Guaspari and Solovay
    "□p → □p ≼ □p",
    "□p ≼ □q → □p",
    "□p ≼ □q ∧ □q ≼ □r → □p ≼ □r",
    "□p ∨ □q → □p ≼ □q ∨ □q ≺ □p",
    "□p ≺ □q → □p ≼ □q",
    "□p ≼ □q → ¬(□q ≺ □p)",
    "□p ∧ ¬□q → □p ≺ □q",
    # the order axioms of de Jongh, and what he derives from them
    "□p → □p ≼ □q ∨ □q ≼ □p",
    "□p ≺ □q → □p",
    "□p ≺ □q ∧ □q ≼ □r → □p ≺ □r",
    "□p ≺ □q ↔ □p ≼ □q ∧ ¬(□q ≼ □p)",
    "□p ≺ □q → ¬(□q ≺ □p)",
    "□p ≺ □q ∧ □q ≺ □r → □p ≺ □r",
    "□p ≼ □q ∧ □q ≺ □r → □p ≺ □r",
    "¬(□p ≺ □p)",
    # Σ-completeness: boxed formulas and comparisons are provable if they hold
    "□p ≺ □q → □(□p ≺ □q)",
    "□p ≼ □q → □(□p ≼ □q)",
    "□p ≺ □q ∨ □r → □(□p ≺ □q ∨ □r)",
    "□p ≼ □q → □□(□p ≼ □q ∧ □p)",
    # boxes of comparisons, compared
    "□(□p ≺ □q) ≼ □r → □(□p ≺ □q)",
    "□p ≺ □q ∧ ◇⊤ → □(□p ≺ □q) ≺ □(□q ≺ □p)",
    # a proof of ⊤ before any of ⊥ is provable, though not a theorem (Guaspari and Solovay 2.4),
    # and so on up (de Jongh, Remark 11)
    "□(□⊤ ≺ □⊥)",
    "□□(□⊤ ≺ □□⊥)",
    "□□□(□⊤ ≺ □□□⊥)",
    "¬□⊥ → □⊤ ≺ □⊥",
    "□⊥ → □p ≼ □q ∨ □q ≺ □p",
    # Rosser's theorem, for a Rosser sentence R ↔ □¬R ≺ □R
    "⊡(R ↔ □¬R ≺ □R) → (□R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → (□¬R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → ¬□R ∧ ¬□¬R)",
    "⊡(R ↔ □¬R ≺ □R) ∧ □¬R ∧ ◇⊤ → R",
    "⊡(R ↔ □¬R ≺ □R) ∧ □R ∧ ◇⊤ → ¬R",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → ¬R)",
    # the sentence that it is proved provable before it is proved is provable
    "⊡(Π ↔ □□Π ≺ □Π) → □Π",
    # GL's theorems are theorems
    "□(□(□p ≺ □q) → □p ≺ □q) → □(□p ≺ □q)",
    "□(□p ≼ □q → r) → (□(□p ≼ □q) → □r)",
]

NON_THEOREMS = [
    # what it takes a rule, □A / A, to prove (Guaspari and Solovay 2.4; de Jongh, Remark 11)
    "□⊤ ≺ □⊥",
    "□(□⊤ ≺ □□⊥)",
    "□□(□⊤ ≺ □□□⊥)",
    # nothing settles which of two theorems is proved first
    "□⊤ ≼ □p",
    "□p → □⊤ ≼ □p",
    "□⊥ → □p ≼ □q",
    "□(p ↔ q) → (□p ≺ □r → □q ≺ □r)",
    "□(p ↔ q) → (□p ≼ □q)",
    "□p ∧ □q → □(p ∧ q) ≼ □p",
    "□p ≺ □q → □(□p ≺ □q) ≺ □(□q ≺ □p)",
    # the order axioms, with too little assumed or too much concluded
    "□p ≼ □p",
    "□p ≼ □q ∨ □q ≼ □p",
    "□p ≼ □q → □q",
    "□p ≼ □q → □p ≺ □q",
    "□p ≼ □q ∧ □q ≼ □p → □p ≺ □q ∨ □q ≺ □p",
    "□p ≼ □q ∧ □r ≼ □q → □p ≼ □r",
    "□p → □p ≺ □q ∨ □q ≺ □p",
    "¬(□p ≼ □q) → □q ≺ □p",
    # the negation of a comparison need not be provable
    "¬(□p ≼ □q) → □¬(□p ≼ □q)",
    "¬(□p ≺ □q) → □¬(□p ≺ □q)",
    # a Rosser sentence that only happens to be one, and what consistency is needed for
    "(R ↔ □¬R ≺ □R) → (□R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → ¬□R",
    "⊡(R ↔ □¬R ≺ □R) → ¬□¬R",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → R)",
    "⊡(R ↔ □¬R ≺ □R) → ¬R",
    # Rosser sentences need not be equivalent
    "⊡(p ↔ □¬p ≺ □p) ∧ ⊡(q ↔ □¬q ≺ □q) → (p ↔ q)",
    # GL's non-theorems are not theorems
    "□(□p ≺ □q) → □p ≺ □q",
    "□p ≺ □q → q",
]

SENTENCES = THEOREMS + NON_THEOREMS


@pytest.mark.parametrize("sentence", THEOREMS)
def test_theorem(rminus_tableau, rminus_decider, sentence):
    assert rminus_decider.closed(rminus_tableau(sentence))


@pytest.mark.parametrize("sentence", NON_THEOREMS)
def test_non_theorem(rminus_tableau, rminus_decider, sentence):
    assert not rminus_decider.closed(rminus_tableau(sentence))


@pytest.mark.parametrize("A", SENTENCES)
def test_semantics(rminus_tableau, rminus_decider, A):
    """The decider's verdict is that of the models of R⁻."""
    t = rminus_tableau(A)
    assert rminus_decider.closed(t) == theorem(sentence(t))


@pytest.mark.parametrize("sentence", GL_THEOREMS + GL_NON_THEOREMS)
def test_conservative(rminus_tableau, rminus_decider, tableau, decider, sentence):
    """R⁻ proves no more sentences of GL than GL does: the two deciders agree on them."""
    assert rminus_decider.closed(rminus_tableau(sentence)) == decider.closed(tableau(sentence))


@pytest.mark.parametrize("sentence", ["□(p", "p ≺ q", "□p ≺ q", "¬□p ≺ □q", "□p ≺ □q ≺ □r", "□p ≼", "≺ □p"])
def test_parse_error(rminus_decider, sentence):
    """What `≺` and `≼` compare must be written as boxed formulas."""
    with pytest.raises(ValueError):
        rminus_decider.tableau(sentence)


def test_parse(rminus_tableau, rminus_decider):
    """Comparisons bind tighter than the binary connectives, and their boxes take what `□`
    takes."""
    spelled = rminus_decider.sentence_tex(rminus_tableau("□p ≺ □q ∧ □¬p ≼ □□q → r"))
    assert spelled == rminus_decider.sentence_tex(rminus_tableau("((□p ≺ □q) ∧ (□(¬p) ≼ □(□q))) → r"))


def test_tex(rminus_tableau, rminus_decider):
    t = rminus_tableau("□(□φ ≺ □ψ) ∨ ¬(□φ ≼ □ψ)")
    assert rminus_decider.sentence_tex(t) == (
        r"\Box (\Box \varphi \prec \Box \psi) \lor \lnot (\Box \varphi \preccurlyeq \Box \psi)"
    )
    tex = rminus_decider.tex(t)
    assert tex.startswith(r"\begin{prooftree}") and r"[{\lnot (\Box \varphi \prec \Box \psi), 1}" in tex
