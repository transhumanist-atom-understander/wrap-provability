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


@pytest.mark.parametrize("method", ["closed", "tex", "sentence_tex", "models_tex", "models_lean", "lean"])
def test_parse_error(decider, method):
    with pytest.raises(ValueError):
        getattr(decider, method)("□(p")


def test_tex(decider):
    assert decider.sentence_tex("□(□φ → φ) → □φ") == r"\Box (\Box \ensuremath{\varphi} \to \ensuremath{\varphi}) \to \Box \ensuremath{\varphi}"
    tex = decider.tex("□(□φ → φ) → □φ")
    assert tex.startswith(r"\begin{prooftree}") and r"[{\lnot \Box \ensuremath{\varphi}, 0}" in tex


def test_letters(decider):
    """A sentence letter's Greek letters and other such characters are LaTeX commands in LaTeX,
    as `pylatexenc` gives them, in an `\\ensuremath` that ends the command, whatever comes next;
    the rest of the letter is as it is: its braces, and LaTeX that it has already."""
    assert decider.sentence_tex(r"□p_{1} → φ1 ∨ \varphi ∨ {0}") == r"\Box p_{1} \to (\ensuremath{\varphi}1 \lor (\varphi \lor {0}))"
    assert decider.sentence_tex("φx → xφ") == r"\ensuremath{\varphi}x \to x\ensuremath{\varphi}"
    assert r"[{\lnot (p_{1} \to \ensuremath{\varphi}), 0}" in decider.tex("p_{1} → φ")
    [model] = decider.models_tex("¬α_{2}")
    assert r"$\Vdash \ensuremath{\alpha}_{2}$" in model
    # no letter at all, and more than ten
    assert decider.sentence_tex("□⊥ → ⊥") == r"\Box \bot \to \bot"
    letters = "a b c d e f g h i j k φ".split()
    assert decider.sentence_tex(" ∧ ".join(letters)).count(r"\varphi") == 1
    assert decider.sentence_tex(" ∧ ".join(reversed(letters))).startswith(r"\ensuremath{\varphi} \land (k \land (j ")


def test_claim(decider):
    """A tableau for a sentence of GL claims that it is a theorem of GL, or that it is not."""
    assert "□(□p → p) → □p is a theorem of GL" in decider.lean("□(□p → p) → □p")
    assert "□p → p is not a theorem of GL" in decider.lean("□p → p")


def worlds(model):
    """The lines of a model's worlds: each a node of the tree, nested in the node of the world
    just above it, which the indentation shows."""
    return [line for line in model.splitlines() if line.lstrip().startswith("[{$w_")]


def test_models_tex(decider):
    assert decider.models_tex("□(□p → p) → □p") == []
    # one world, where φ doesn't hold: by a world are the letters that do
    [model] = decider.models_tex("□φ → φ")
    assert model.startswith(r"\begin{forest}") and model.endswith(r"\end{forest}")
    assert worlds(model) == [r"  [{$w_{0}$\nodepart{two}}]"]
    [model] = decider.models_tex("φ → □φ")
    assert worlds(model) == [r"  [{$w_{0}$\nodepart{two}$\Vdash \ensuremath{\varphi}$}", r"    [{$w_{1}$\nodepart{two}}]]"]
    # an open branch for each way that p ∨ q → p ∧ q fails
    assert [worlds(m) for m in decider.models_tex("p ∨ q → p ∧ q")] == [
        [r"  [{$w_{0}$\nodepart{two}$\Vdash p$}]"], [r"  [{$w_{0}$\nodepart{two}$\Vdash q$}]"]]
    # two worlds below the first, and one below the second of them: a tree, without the arrow
    # that transitivity adds
    [model] = decider.models_tex("((□□Π ∧ ¬□Π) → Π) ∧ (Π → □Π) → □Π")
    assert worlds(model) == [
        r"  [{$w_{0}$\nodepart{two}}",
        r"    [{$w_{1}$\nodepart{two}}]",
        r"    [{$w_{2}$\nodepart{two}}",
        r"      [{$w_{3}$\nodepart{two}}]]]"]
    # the room a letter takes is the room it takes in print, however it was typed
    [typed], [printed] = decider.models_tex(r"¬(\varphi ∧ \psi)"), decider.models_tex("¬(φ ∧ ψ)")
    assert r"$\Vdash \varphi, \psi$" in typed
    assert typed == printed.replace(r"\ensuremath{\varphi}", r"\varphi").replace(r"\ensuremath{\psi}", r"\psi")
