"""The decider's verdicts on sentences of GL, those with no witness comparison, whose verdict is
well known or follows from GL's semantics on finite transitive irreflexive frames. For these the
tableau is GL's, and decides the sentence."""

import pytest

THEOREMS = [
    # Löb's axiom and what comes with it
    "□(□p → p) → □p",
    "□(□p → p) ↔ □p",
    "□(□(□p → p) → □p)",
    "□(□(q ∧ ◇r) → (q ∧ ◇r)) → □(q ∧ ◇r)",
    "□p → □□p",
    "□(□p → q) → □(□p → □q)",
    "◇¬p → ◇(□p ∧ ¬p)",
    "◇p → ◇(p ∧ □¬p)",
    # the second incompleteness theorem, both ways round
    "¬□⊥ → ¬□¬□⊥",
    "◇⊤ → ◇□⊥",
    "□◇⊤ → □⊥",
    # fixed points: ¬□⊥ for ¬□p, ⊤ for □p, and their uniqueness
    "⊡(p ↔ ¬□p) → (p ↔ ¬□⊥)",
    "⊡(p ↔ □p) → p",
    "(⊡(p ↔ ¬□p) ∧ ⊡(q ↔ ¬□q)) → (p ↔ q)",
    # K, and the duality of □ and ◇
    "□(p → q) → (□p → □q)",
    "□(p → q) → (◇p → ◇q)",
    "□(p ∧ q) ↔ (□p ∧ □q)",
    "◇(p ∨ q) ↔ (◇p ∨ ◇q)",
    "(□p ∨ □q) → □(p ∨ q)",
    "◇◇p → ◇p",
    "¬◇p ↔ □¬p",
    "◇p ∨ □¬p",
    "□⊥ → □p",
    "□⊤",
    # classical tautologies, for the branching rules
    "((p → q) → p) → p",
    "(p → q) → (¬q → ¬p)",
    "p ∨ ¬p",
    "¬(p ∧ ¬p)",
    "((p ↔ q) ↔ r) ↔ (p ↔ (q ↔ r))",
    "⊥ → p",
    "¬⊤ → p",
    # sentence letters other than a Latin letter
    "□(□φ → φ) → □φ",
    "□(p1 → p2) → (□p1 → □p2)",
]

NON_THEOREMS = [
    # axioms of other modal logics
    "□p → p",
    "p → □p",
    "□p → ◇p",
    "p → □◇p",
    "◇p → □◇p",
    "□◇p → ◇□p",
    "□(⊡p → q) ∨ □(⊡q → p)",
    # the converses of what GL proves
    "□□p → □p",
    "◇p → ◇◇p",
    "(□p → □q) → □(p → q)",
    "□(p ∨ q) → (□p ∨ □q)",
    "□(p ↔ ¬□p) → (p ↔ ¬□⊥)",
    # consistency, and what it doesn't give
    "◇⊤",
    "¬□⊥ → □¬□⊥",
    "◇⊤ → (□p → p)",
    "□(□p → p)",
    "p ↔ ¬□p",
    "□p ∨ □¬p",
    # classical non-tautologies
    "(p → q) → (q → p)",
    "(p ↔ q) → (p ∧ q)",
    "p",
]


@pytest.mark.parametrize("sentence", THEOREMS)
def test_theorem(tableau, decider, sentence):
    assert decider.closed(tableau(sentence))


@pytest.mark.parametrize("sentence", NON_THEOREMS)
def test_non_theorem(tableau, decider, sentence):
    assert not decider.closed(tableau(sentence))


def test_parse_error(decider):
    with pytest.raises(ValueError):
        decider.tableau("□(p")


def test_tex(tableau, decider):
    t = tableau("□(□φ → φ) → □φ")
    assert decider.sentence_tex(t) == r"\Box (\Box \varphi \to \varphi) \to \Box \varphi"
    tex = decider.tex(t)
    assert tex.startswith(r"\begin{prooftree}") and r"[{\lnot \Box \varphi, 0}" in tex


def test_claim(tableau):
    """A tableau for a sentence of GL claims that it is a theorem of GL, or that it is not."""
    assert "□(□p → p) → □p is a theorem of GL" in tableau("□(□p → p) → □p")
    assert "□p → p is not a theorem of GL" in tableau("□p → p")
