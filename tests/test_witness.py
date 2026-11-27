"""The decider's verdicts on sentences with witness comparisons, and a check of them.

Its rules for comparisons are complete for Guaspari and Solovay's R⁻: a tableau closes if its
sentence is a theorem of R⁻ and doesn't if it is not. So there are two lists, theorems, with
the ones of the tableau notebook first, and non-theorems.

`test_models` has `witness_semantics` decide each sentence again from the models of R⁻, by
brute force, and `test_random` does the same for sentences at random: the two must agree.
"""

import random

import pytest

from witness_semantics import sentence, theorem

THEOREMS = [
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
    "⊡(J ↔ □□J ≺ □(□⊥ → J)) → ((¬J ∧ □(□⊥ → J)) → □¬J)",
    # no circle of comparisons with a strict one in it, however long
    "¬(□p ≺ □q ∧ □q ≺ □r ∧ □r ≺ □p)",
    "¬(□p ≼ □q ∧ □q ≼ □r ∧ □r ≼ □s ∧ □s ≺ □p)",
    "□p ≼ □q ∧ □q ≼ □r ∧ □r ≼ □p → □q ≼ □p",
    "□p ≺ □q ∧ □q ≼ □r → □p ≺ □r",
    "□p ≺ □q ↔ □p ≼ □q ∧ ¬(□q ≼ □p)",
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
    # comparisons that go round, with no strict one among them
    "¬(□p ≼ □q ∧ □q ≼ □r ∧ □r ≼ □p)",
    "□p ≼ □q ∧ □q ≼ □r → □p ≺ □r",
    # GL's non-theorems are not theorems
    "□(□p ≺ □q) → □p ≺ □q",
    "□p ≺ □q → q",
]

SENTENCES = THEOREMS + NON_THEOREMS


@pytest.mark.parametrize("sentence", THEOREMS)
def test_theorems(decider, sentence):
    assert decider.closed(sentence)


@pytest.mark.parametrize("sentence", NON_THEOREMS)
def test_non_theorems(decider, sentence):
    assert not decider.closed(sentence)


@pytest.mark.parametrize("A", SENTENCES)
def test_models(decider, A):
    """The lists are right about R⁻."""
    assert theorem(sentence(decider.lean(A))) == (A in THEOREMS)


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
        if ("≺" in A or "≼" in A) and A.count("□") <= 4 and A not in found:
            found.append(A)
    return found


@pytest.mark.parametrize("A", sentences(seed=1979, count=300, depth=4))
def test_random(decider, A):
    """On sentences at random, too, the decider proves the theorems of R⁻ and no others."""
    assert decider.closed(A) == theorem(sentence(decider.lean(A)))


@pytest.mark.parametrize("sentence", ["□(p", "p ≺ q", "□p ≺ q", "¬□p ≺ □q", "□p ≺ □q ≺ □r", "□p ≼", "≺ □p"])
def test_parse_error(decider, sentence):
    """What `≺` and `≼` compare must be written as boxed formulas."""
    with pytest.raises(ValueError):
        decider.closed(sentence)


def test_parse(decider):
    """Comparisons bind tighter than the binary connectives, and their boxes take what `□`
    takes."""
    spelled = decider.sentence_tex("□p ≺ □q ∧ □¬p ≼ □□q → r")
    assert spelled == decider.sentence_tex("((□p ≺ □q) ∧ (□(¬p) ≼ □(□q))) → r")


def test_tex(decider):
    """A comparison that fails is split into its first formula failing and the converse
    comparison; one that holds at a world held at the world that started it, or its second
    formula didn't hold there."""
    assert decider.sentence_tex("□(□φ ≺ □ψ)") == r"\Box (\Box \varphi \prec \Box \psi)"
    tex = decider.tex("□(□φ ≺ □ψ)")
    assert tex.startswith(r"\begin{prooftree}") and r"[{\Box \psi \preccurlyeq \Box \varphi, 1}" in tex
    assert r"[{(\Box \psi \preccurlyeq \Box \varphi) \lor \lnot \Box \varphi, 0}" in tex


@pytest.mark.parametrize("sentence", [
    "□(□p → p) → □p", "◇p → □◇p", "((p ↔ q) ↔ r) ↔ (p ↔ (q ↔ r))", "(□p ∨ □q) → □(p ∨ ⊥ ∨ q)",
    "⊡(Π ↔ □□Π ≺ □Π) → □Π", "¬(□p ≺ □q ∧ □q ≺ □r ∧ □r ≺ □p)", "□p ≼ □q → □p ≺ □q"])
def test_lean(decider, sentence):
    """The Lean file of a tableau is one that Lean reads, and the tableau it defines is the one
    it is the file of: Lean, having read it, prints it again."""
    file = decider.lean(sentence)
    [printed] = decider._run(file + "\n#eval IO.print t.lean").messages
    assert printed.data == file


def test_claim(decider):
    """A tableau that closes claims a theorem of R⁻, and one that doesn't a non-theorem."""
    assert "□(□¬⊥ ≺ □⊥) is a theorem of R⁻" in decider.lean("□(□⊤ ≺ □⊥)")
    assert "□¬⊥ ≺ □⊥ is not a theorem of R⁻" in decider.lean("□⊤ ≺ □⊥")


def test_circle(decider):
    """A branch closes on comparisons at a world that go round, one of them strict."""
    assert "(.cycle 0 [(.prec " in decider.lean("¬(□p ≺ □q ∧ □q ≺ □r ∧ □r ≺ □p)")


def test_models_tex(decider):
    """A model has an order at a world where the branch has one boxed formula witnessed before
    another: the boxed formulas are named where the worlds are, and spelled out below them."""
    [tex] = decider.models_tex("□p ≼ □q ∧ □q ≼ □p → ¬(□p ≺ □r)")
    assert r"$\Vdash b_{1} \approx b_{2} \prec b_{3}$" in tex
    assert r"{$b_{1} = \Box p$}" in tex and r"{$b_{3} = \Box r$}" in tex
    # and none where it has them witnessed together, as they are with no order
    [tex] = decider.models_tex("□p ≼ □q → □p ≺ □q")
    assert r"[{$w_{0}$\nodepart{two}}]" in tex and "b_{1}" not in tex
