"""The witness decider's verdicts on sentences with witness comparisons, and two checks of them.

Its rules for comparisons are persistence and true before false: they prove theorems of
Guaspari and Solovay's R⁻, but not all of them, since they say nothing of the order of boxed
formulas that come to hold together. So there are three lists: theorems of R⁻ it proves, with
the ones of the tableau notebook first; theorems of R⁻ it doesn't; and sentences that are not
theorems of R⁻.

No verifier checks these tableaux. In its place, `test_models` has `witness_semantics` decide
each sentence again from the models of R⁻, by brute force, and `test_axioms` has GL's decider
decide whether the sentence follows from the axioms that the rules replace, taken as premises:
the witness decider's tableau closes exactly when it does. A sentence can be added to `PROVED`
or `NOT_PROVED` without knowing which it belongs in: `test_axioms` will say, if its tableau
with the axioms as premises is small enough to add it to `SMALL` too.
"""

import random

import pytest

from test_gl import NON_THEOREMS as GL_NON_THEOREMS
from test_gl import THEOREMS as GL_THEOREMS
from witness_semantics import reduction, sentence, theorem

PROVED = [
    # the notebook: a proof of ⊤ comes before any of ⊥, if there is none of ⊥, and provably so;
    # the Parikh sentence; the two halves of Rosser's theorem
    "◇⊤ → □⊤ ≺ □⊥",
    "□(□⊤ ≺ □⊥)",
    "⊡(Π ↔ □□Π ≺ □Π) → □Π",
    "⊡(R ↔ □¬R ≺ □R) ∧ □¬R ∧ ◇⊤ → R",
    "⊡(R ↔ □¬R ≺ □R) ∧ □R ∧ ◇⊤ → ¬R",
    # true before false, and persistence
    "□p ∧ ¬□q → □p ≺ □q",
    "□p ∧ ¬□q → □p ≼ □q",
    "□p ≺ □q → □(□p ≺ □q)",
    "□p ≼ □q → □(□p ≼ □q)",
    "□p ≺ □q ∨ □r → □(□p ≺ □q ∨ □r)",
    "□p ≼ □q → □□(□p ≼ □q ∧ □p)",
    # the two together: true before false at a world, for a comparison at a world it sees
    "□p ∧ ¬□q → □(□p ≺ □q)",
    "□¬(□p ≺ □q) → (□p → □q)",
    # a comparison that holds: its first formula is true, and false is not before true
    "□p ≺ □q → □p",
    "□p ≼ □q → □p",
    "□q ∧ ¬□p → ¬(□p ≺ □q)",
    "□q ∧ ¬□p → □¬(□p ≺ □q)",
    "◇(□p ≺ □q) ∧ □q → □p",
    "□p ≺ □q → □(□q → □p)",
    "□(p → q) ∧ □p ≺ □r → □(□r → □q)",
    "□(□p ≺ □q) ≼ □r → □(□p ≺ □q)",
    # so on up (Guaspari and Solovay 2.4; de Jongh, Remark 11)
    "□□(□⊤ ≺ □□⊥)",
    "□□□(□⊤ ≺ □□□⊥)",
    # Rosser's theorem, for a Rosser sentence R ↔ □¬R ≺ □R
    "⊡(R ↔ □¬R ≺ □R) → (□R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → (□¬R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → ¬□R ∧ ¬□¬R)",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → ¬R)",
    # provable fixed points (de Jongh and Montagna 1.2, 1.5, 6.1, 7.1, 7.4), a refutable one (5.1)
    "⊡(c ↔ □⊤ ≺ □c) → □c",
    "⊡(c ↔ □□□c ≺ □□c ∧ □□c ≺ □c) → □□c",
    "⊡(c ↔ □□(c ∨ q) ≺ □c) → □c",
    "⊡(c ↔ □(□□c ≺ □c) ≺ □c) → □c",
    "⊡(c ↔ □d ≺ □c) ∧ ⊡(d ↔ □□c ≺ □d) → □c",
    "⊡(c ↔ □¬c ≺ □□¬c) → □¬c",
    # GL's theorems are theorems
    "□(□(□p ≺ □q) → □p ≺ □q) → □(□p ≺ □q)",
    "□(□p ≼ □q → r) → (□(□p ≼ □q) → □r)",
]

NOT_PROVED = [
    # ≼ is a total preorder of the boxed formulas that hold, and ≺ is its strict part
    "□p → □p ≼ □p",
    "□p ≼ □q ∧ □q ≼ □r → □p ≼ □r",
    "□p ∨ □q → □p ≼ □q ∨ □q ≺ □p",
    "□p → □p ≼ □q ∨ □q ≼ □p",
    "□p ≺ □q → □p ≼ □q",
    "□p ≼ □q → ¬(□q ≺ □p)",
    "□p ≺ □q → ¬(□q ≺ □p)",
    "¬(□p ≺ □p)",
    "□p ≺ □q ∧ □q ≺ □r → □p ≺ □r",
    "□⊥ → □p ≼ □q ∨ □q ≺ □p",
    # so the order of two boxed formulas that hold is settled
    "¬(□p ≺ □q) ∧ □q → □¬(□p ≺ □q)",
    "□p ≺ □q ∧ ◇⊤ → □(□p ≺ □q) ≺ □(□q ≺ □p)",
    # a provable fixed point that needs it (de Jongh and Montagna, after 3.5)
    "⊡(c ↔ □□c ≺ □(□⊥ → c)) → □□c",
]

NON_THEOREMS = [
    # the notebook: what it takes R's rule, □A / A, to prove
    "□⊤ ≺ □⊥",
    "⊡(Π ↔ □□Π ≺ □Π) → Π",
    "□(□⊤ ≺ □□⊥)",
    "□□(□⊤ ≺ □□□⊥)",
    # nothing settles which of two theorems is proved first
    "□⊤ ≼ □p",
    "□p → □⊤ ≼ □p",
    "□(p ↔ q) → (□p ≺ □r → □q ≺ □r)",
    "□p ∧ □q → □(p ∧ q) ≼ □p",
    # the axioms, with too little assumed or too much concluded
    "□p ≼ □p",
    "□p ≼ □q ∨ □q ≼ □p",
    "□p ≺ □q → □q",
    "□p ≼ □q → □p ≺ □q",
    "□p → □p ≺ □q ∨ □q ≺ □p",
    "¬(□p ≼ □q) → □q ≺ □p",
    "□p → □p ≺ □q",
    "¬(□p ≺ □q) → □(□p → □q) ∨ □p ≺ □q",
    # the negation of a comparison need not persist
    "¬(□p ≺ □q) → □¬(□p ≺ □q)",
    "¬(□p ≼ □q) → □¬(□p ≼ □q)",
    # a Rosser sentence that only happens to be one, and what consistency is needed for
    "(R ↔ □¬R ≺ □R) → (□R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → ¬□R",
    "⊡(R ↔ □¬R ≺ □R) → ¬□¬R",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → R)",
    "⊡(R ↔ □¬R ≺ □R) → ¬R",
    # GL's non-theorems are not theorems
    "□(□p ≺ □q) → □p ≺ □q",
    "□p ≺ □q → q",
]

SENTENCES = PROVED + NOT_PROVED + NON_THEOREMS

# The sentences that `test_axioms` has GL's decider decide with the axioms as premises: those
# for which that tableau has hundreds of lines, not thousands. That the others are spared it is
# what the rules are for: the tableau for the Parikh sentence has 14,000 lines that way, and 52
# with the rules.
SMALL = [
    "◇⊤ → □⊤ ≺ □⊥",
    "□(□⊤ ≺ □⊥)",
    "⊡(R ↔ □¬R ≺ □R) ∧ □¬R ∧ ◇⊤ → R",
    "⊡(R ↔ □¬R ≺ □R) ∧ □R ∧ ◇⊤ → ¬R",
    "□p ∧ ¬□q → □p ≺ □q",
    "□p ∧ ¬□q → □p ≼ □q",
    "□p ≺ □q → □(□p ≺ □q)",
    "□p ≼ □q → □(□p ≼ □q)",
    "□p ≺ □q ∨ □r → □(□p ≺ □q ∨ □r)",
    "□p ≼ □q → □□(□p ≼ □q ∧ □p)",
    "□p ∧ ¬□q → □(□p ≺ □q)",
    "□¬(□p ≺ □q) → (□p → □q)",
    "□p ≺ □q → □p",
    "□p ≼ □q → □p",
    "□q ∧ ¬□p → ¬(□p ≺ □q)",
    "□q ∧ ¬□p → □¬(□p ≺ □q)",
    "□p ≺ □q → □(□q → □p)",
    "□(p → q) ∧ □p ≺ □r → □(□r → □q)",
    "□(□p ≺ □q) ≼ □r → □(□p ≺ □q)",
    "⊡(R ↔ □¬R ≺ □R) → (□R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → (□¬R → □⊥)",
    "⊡(R ↔ □¬R ≺ □R) → (◇⊤ → ¬R)",
    "⊡(c ↔ □⊤ ≺ □c) → □c",
    "□(□(□p ≺ □q) → □p ≺ □q) → □(□p ≺ □q)",
    "□(□p ≼ □q → r) → (□(□p ≼ □q) → □r)",
    "□p → □p ≼ □p",
    "□p ≺ □q → □p ≼ □q",
    "□p ≼ □q → ¬(□q ≺ □p)",
    "□p ≺ □q → ¬(□q ≺ □p)",
    "¬(□p ≺ □p)",
    "¬(□p ≺ □q) ∧ □q → □¬(□p ≺ □q)",
    "□⊤ ≺ □⊥",
    "□⊤ ≼ □p",
    "□p → □⊤ ≼ □p",
    "□p ∧ □q → □(p ∧ q) ≼ □p",
    "□p ≺ □q → □q",
    "□p ≼ □q → □p ≺ □q",
    "□p → □p ≺ □q",
    "⊡(R ↔ □¬R ≺ □R) → ¬□R",
    "⊡(R ↔ □¬R ≺ □R) → ¬□¬R",
    "⊡(R ↔ □¬R ≺ □R) → ¬R",
    "□p ≺ □q → q",
]


@pytest.mark.parametrize("sentence", PROVED)
def test_proved(witness_tableau, witness_decider, sentence):
    assert witness_decider.closed(witness_tableau(sentence))


@pytest.mark.parametrize("sentence", NOT_PROVED + NON_THEOREMS)
def test_not_proved(witness_tableau, witness_decider, sentence):
    assert not witness_decider.closed(witness_tableau(sentence))


@pytest.mark.parametrize("A", SENTENCES)
def test_models(witness_tableau, A):
    """The lists are right about R⁻: in particular, what the decider proves is a theorem."""
    assert theorem(sentence(witness_tableau(A))) == (A not in NON_THEOREMS)


@pytest.mark.parametrize("A", SMALL)
def test_axioms(witness_tableau, witness_decider, tableau, decider, A):
    """The rules do what the axioms they replace do as premises: the tableau closes exactly
    when GL's decider proves the sentence from them."""
    t = witness_tableau(A)
    assert witness_decider.closed(t) == decider.closed(tableau(reduction(sentence(t)))) == (A in PROVED)


def sentences(seed, count, depth):
    """`count` sentences with a comparison, of connectives nested up to `depth` deep, at random:
    ones nobody thought of."""
    rng = random.Random(seed)

    def formula(depth):
        kind = rng.random()
        if depth == 0 or kind < 0.15:
            return rng.choice(["p", "q", "⊥", "⊤"])
        if kind < 0.3:
            return f"¬{formula(depth - 1)}"
        if kind < 0.5:
            return f"□{formula(depth - 1)}"
        if kind < 0.75:
            return f"(□{formula(depth - 1)} {rng.choice('≺≺≼')} □{formula(depth - 1)})"
        return f"({formula(depth - 1)} {rng.choice('∧∨→→↔')} {formula(depth - 1)})"

    found = []
    while len(found) < count:
        A = formula(depth)
        if ("≺" in A or "≼" in A) and A.count("□") <= 5 and A not in found:
            found.append(A)
    return found


@pytest.mark.parametrize("A", sentences(seed=1979, count=200, depth=4))
def test_random(witness_tableau, witness_decider, A):
    """On sentences at random, too, the decider proves only theorems of R⁻."""
    t = witness_tableau(A)
    if witness_decider.closed(t):
        assert theorem(sentence(t))


@pytest.mark.parametrize("sentence", GL_THEOREMS + GL_NON_THEOREMS)
def test_conservative(witness_tableau, witness_decider, tableau, decider, sentence):
    """On the sentences of GL the two deciders agree."""
    assert witness_decider.closed(witness_tableau(sentence)) == decider.closed(tableau(sentence))


@pytest.mark.parametrize("sentence", ["□(p", "p ≺ q", "□p ≺ q", "¬□p ≺ □q", "□p ≺ □q ≺ □r", "□p ≼", "≺ □p"])
def test_parse_error(witness_decider, sentence):
    """What `≺` and `≼` compare must be written as boxed formulas."""
    with pytest.raises(ValueError):
        witness_decider.tableau(sentence)


def test_parse(witness_tableau, witness_decider):
    """Comparisons bind tighter than the binary connectives, and their boxes take what `□`
    takes."""
    spelled = witness_decider.sentence_tex(witness_tableau("□p ≺ □q ∧ □¬p ≼ □□q → r"))
    assert spelled == witness_decider.sentence_tex(witness_tableau("((□p ≺ □q) ∧ (□(¬p) ≼ □(□q))) → r"))


def test_tex(witness_tableau, witness_decider):
    """The rules for comparisons add implications between the boxed formulas they compare."""
    t = witness_tableau("□(□φ ≺ □ψ)")
    assert witness_decider.sentence_tex(t) == r"\Box (\Box \varphi \prec \Box \psi)"
    tex = witness_decider.tex(t)
    assert tex.startswith(r"\begin{prooftree}") and r"[{\Box \varphi \to \Box \psi, 0}" in tex


def test_claim(witness_tableau):
    """A tableau that closes claims a theorem of R⁻; one that doesn't claims no more than that
    its rules were not enough."""
    assert "□(□¬⊥ ≺ □⊥) is a theorem of R⁻" in witness_tableau("□(□⊤ ≺ □⊥)")
    assert "does not follow from persistence and true before false" in witness_tableau("□⊤ ≺ □⊥")
