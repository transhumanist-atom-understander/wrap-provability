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
def test_theorem(decider, sentence):
    assert decider.closed(sentence)


@pytest.mark.parametrize("sentence", NON_THEOREMS)
def test_non_theorem(decider, sentence):
    assert not decider.closed(sentence)


@pytest.mark.parametrize("method", ["closed", "tex", "sentence_tex", "models_tex", "lean"])
def test_parse_error(decider, method):
    with pytest.raises(ValueError):
        getattr(decider, method)("□(p")


def test_tex(decider):
    assert decider.sentence_tex("□(□φ → φ) → □φ") == r"\Box (\Box \varphi \to \varphi) \to \Box \varphi"
    tex = decider.tex("□(□φ → φ) → □φ")
    assert tex.startswith(r"\begin{prooftree}") and r"[{\lnot \Box \varphi, 0}" in tex


def test_letters(decider):
    """A sentence letter's Greek letters and other such characters are LaTeX commands in LaTeX,
    and the rest of it is as it is: its braces, and LaTeX that it has already."""
    assert decider.sentence_tex(r"□p_{1} → φ1 ∨ \varphi ∨ {0}") == r"\Box p_{1} \to (\varphi1 \lor (\varphi \lor {0}))"
    assert r"[{\lnot (p_{1} \to \varphi), 0}" in decider.tex("p_{1} → φ")
    [model] = decider.models_tex("α_{2}")
    assert r"{$\,\Vdash \lnot \alpha_{2}$}" in model
    # no letter at all, and more than ten
    assert decider.sentence_tex("□⊥ → ⊥") == r"\Box \bot \to \bot"
    letters = "a b c d e f g h i j k φ".split()
    assert decider.sentence_tex(" ∧ ".join(letters)).count(r"\varphi") == 1
    assert decider.sentence_tex(" ∧ ".join(reversed(letters))).startswith(r"\varphi \land (k \land (j ")


def test_claim(decider):
    """A tableau for a sentence of GL claims that it is a theorem of GL, or that it is not."""
    assert "□(□p → p) → □p is a theorem of GL" in decider.lean("□(□p → p) → □p")
    assert "□p → p is not a theorem of GL" in decider.lean("□p → p")


def test_models_tex(decider):
    assert decider.models_tex("□(□p → p) → □p") == []
    assert decider.models_tex("□φ → φ") == [r"""\begin{tikzpicture}[>=stealth]
  \node[inner sep=2pt] (w0) at (0mm,0mm) {$w_{0}$};
  \node[anchor=west, inner sep=0pt] at (w0.east) {$\,\Vdash \lnot \varphi$};
\end{tikzpicture}"""]
    # an open branch for each way that p ∨ q → p ∧ q fails
    assert [m.splitlines()[2].split("Vdash ")[1] for m in decider.models_tex("p ∨ q → p ∧ q")] == [
        r"p, \lnot q$};", r"q, \lnot p$};"]
    # two worlds started from the first, and one from the second of them: a tree, without the
    # arrow that transitivity adds
    [tex] = decider.models_tex("((□□Π ∧ ¬□Π) → Π) ∧ (Π → □Π) → □Π")
    arrows = [line.strip() for line in tex.splitlines() if "draw" in line]
    assert arrows == [r"\draw[->] (w0.south) -- (w1.north);", r"\draw[->] (w0.south) -- (w2.north);", r"\draw[->] (w2.south) -- (w3.north);"]
    assert tex.count(r"\Vdash \lnot \Pi$") == 3 and "(w2.east)" not in tex
