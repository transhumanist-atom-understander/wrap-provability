"""The decider's verdicts on sentences of GL, and Lean's check of its tableaux by the verifier.

Verification is the real test: it accepts a tableau only if every rule was applied properly and
the sentence is in `LogicGL` when it closed, and has a countermodel when it didn't. So a
sentence need not come with its verdict; the ones below do, as a check on both projects
together, where the verdict is well known or follows from GL's semantics on finite transitive
irreflexive frames.
"""

import pytest

from gltableau import LeanError

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


@pytest.mark.parametrize("sentence", THEOREMS + NON_THEOREMS)
def test_verified(tableau, verifier, sentence):
    verifier.verify(tableau(sentence))


def test_verifier_rejects_a_misapplied_rule(tableau, verifier):
    """A tableau that stops before it should claims a countermodel that isn't one, and one that
    closes without a clash claims a derivation that isn't one: Lean rejects both."""
    with pytest.raises(LeanError):
        verifier.verify(tableau("□(□p → p) → □p").replace("(.closed 1 \"p\")", ".exhausted"))
    with pytest.raises(LeanError):
        verifier.verify(tableau("□p → p").replace(".exhausted", "(.closed 0 \"p\")"))


def test_parse_error(decider):
    with pytest.raises(ValueError):
        decider.tableau("□(p")


def test_tex(tableau, decider):
    t = tableau("□(□φ → φ) → □φ")
    assert decider.sentence_tex(t) == r"\Box (\Box \varphi \to \varphi) \to \Box \varphi"
    tex = decider.tex(t)
    assert tex.startswith(r"\begin{prooftree}") and r"[{\lnot \Box \varphi, 0}" in tex
