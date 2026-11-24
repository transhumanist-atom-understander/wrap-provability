"""Models: the ones a tableau's open branches describe, and what holds in a model.

A model is a Lean term, and every one is a model of R⁻, so what the decider says holds in one
is what its verdicts on non-theorems come down to, and what a model written by hand is taken to
show. `test_countermodels` and `test_random_countermodels` have it check each model that an
open tableau describes: the sentence fails there. `test_sound` has it check the theorems in
models at random: each holds. `test_satisfied` has `witness_semantics` work out again what
holds in a model, for sentences and models at random: the two must agree.
"""

import random

import pytest

import test_gl
import test_witness
from witness_semantics import satisfied, sentence, subformulas, term

THEOREMS = test_gl.THEOREMS + test_witness.THEOREMS
NON_THEOREMS = test_gl.NON_THEOREMS + test_witness.NON_THEOREMS


def models(seed, count, A):
    """`count` models at random, as `witness_semantics` has one, of up to six worlds: at each,
    some of `A`'s letters hold, and some of its boxed subformulas are ordered, some together."""
    rng = random.Random(seed)
    letters = sorted({B[1] for B in subformulas(A) if B[0] == "atom"})
    boxed = sorted((B[1] for B in subformulas(A) if B[0] == "box"), key=repr)

    def world(room):
        order = [[] for _ in range(rng.randint(0, 3))]
        for B in boxed:
            if order and rng.random() < 0.7:
                rng.choice(order).append(B)
        sees = []
        while room[0] and rng.random() < 0.6:
            room[0] -= 1
            sees.append(world(room))
        return {"letters": [p for p in letters if rng.random() < 0.5], "order": order, "sees": sees}

    return [world([5]) for _ in range(count)]


@pytest.mark.parametrize("A", NON_THEOREMS)
def test_countermodels(decider, A):
    """An open branch describes a countermodel, and the LaTeX of the models is that of each."""
    found = decider.models_lean(A)
    assert found and not any(decider.satisfied(A, model) for model in found)
    assert decider.models_tex(A) == [decider.model_tex(model) for model in found]


@pytest.mark.parametrize("A", test_witness.sentences(seed=1979, count=300, depth=4))
def test_random_countermodels(decider, A):
    """On sentences at random, too: one that is not a theorem fails in each of its models."""
    found = decider.models_lean(A)
    assert bool(found) == (not decider.closed(A)) and not any(decider.satisfied(A, model) for model in found)


@pytest.mark.parametrize("A", THEOREMS)
def test_sound(decider, A):
    """A theorem has no model to show, and holds in every model: here, in some at random."""
    assert decider.models_lean(A) == []
    for model in models(seed=A, count=10, A=sentence(decider.lean(A))):
        assert decider.satisfied(A, term(model))


@pytest.mark.parametrize("A", test_witness.sentences(seed=1987, count=200, depth=4))
def test_satisfied(decider, A):
    """What holds in a model is what `witness_semantics` says holds in it."""
    B = sentence(decider.lean(A))
    for model in models(seed=A, count=5, A=B):
        assert decider.satisfied(A, term(model)) == satisfied(B, model)


def test_by_hand(decider):
    """A model written by hand shows a non-theorem with no tableau: here, that two boxed
    formulas can be witnessed in one order at one world and the other at another."""
    model = '{ sees := [{ order := [["□p"], ["□q"]] }, { order := [["□q"], ["□p"]] }] }'
    assert decider.satisfied("◇(□p ≺ □q) ∧ ◇(□q ≺ □p)", model)
    assert not decider.satisfied("¬(◇(□p ≺ □q) ∧ ◇(□q ≺ □p))", model)
    # neither holds at the first world, where neither boxed formula does
    assert not decider.satisfied("□p ≺ □q ∨ □q ≺ □p ∨ □p ∨ □q", model)
    # with no order, the two are witnessed together, at the last world, where every boxed formula holds
    assert decider.satisfied("□p ≼ □q ∧ □q ≼ □p ∧ ¬(□p ≺ □q)", "{}")
    # a letter holds where the model says, and a world sees the worlds below those it sees
    model = '{ letters := ["p"], sees := [{ letters := ["p"], sees := [{}] }] }'
    assert decider.satisfied("p ∧ ◇p ∧ ◇¬p ∧ ¬□p ∧ ◇□p ∧ ◇□⊥", model)
    # true before false: □q first holds at the second world, □p not until the third
    assert decider.satisfied("◇(□q ≺ □p ∧ ¬□p) ∧ □(□p → □q ≺ □p)", '{ sees := [{ letters := ["q"], sees := [{ letters := ["q"] }] }] }')


def test_order(decider):
    """An order is of the boxed formulas that first hold at its world: those of a list
    together, before those of the next, and the others after them, together; what held already
    at the world above was witnessed before them all, whatever the order says."""
    world = lambda order: f'{{ letters := ["p"], sees := [{{ letters := ["p"], order := {order} }}] }}'
    assert decider.satisfied("□(□q ≺ □r ∧ □r ≼ □s ∧ □s ≼ □r ∧ □s ≺ □t ∧ □t ≼ □u ∧ □u ≼ □t)", world('[["□q"], ["□r", "□s"]]'))
    assert decider.satisfied("□p ∧ □(□p ≺ □q ∧ ¬(□q ≼ □p))", world('[["□q"], ["□p"]]'))
    # a formula is the one written, not one equivalent to it
    assert decider.satisfied("□(□q ≺ □(q ∧ q) ∧ □(q ∧ q) ≼ □¬¬q ∧ □¬¬q ≼ □(q ∧ q))", world('[["□q"]]'))


@pytest.mark.parametrize("model", ['{ letters := ["¬p"] }', '{ letters := ["p q"] }', '{ order := [["p"]] }', '{ order := [["□(p"]] }',
                                   '{ sees := [{ order := [["□p ≺ □q"]] }] }', '{ letters := "p" }', "{", "m"])
def test_model_error(decider, model):
    """A model has to be one that Lean reads, of sentence letters and orders of boxed formulas."""
    for method in [lambda: decider.satisfied("p", model), lambda: decider.model_tex(model)]:
        with pytest.raises(ValueError):
            method()


def test_sentence_error(decider):
    with pytest.raises(ValueError):
        decider.satisfied("□(p", "{}")


def test_models_lean(decider):
    """A model is written with the fields that it has something in, each world on a line."""
    assert decider.models_lean("□φ → φ") == ["{}"]
    assert decider.models_lean("p ∨ q → p ∧ q") == ['{ letters := ["p"] }', '{ letters := ["q"] }']
    assert decider.models_lean("((□□Π ∧ ¬□Π) → Π) ∧ (Π → □Π) → □Π") == ["{ sees := [\n  {},\n  { sees := [\n    {} ] } ] }"]
    # an order where the branch has one formula before another: nowhere else
    assert decider.models_lean("□p ∧ □q → □(p ∧ q) ≼ □p") == ['{ order := [["□p"], ["□(p ∧ q)"]] }']
    assert decider.models_lean("□p ≼ □q → □p ≺ □q") == ["{}"]


@pytest.mark.parametrize("A", ["□φ → φ", "□p ∧ □q → □(p ∧ q) ≼ □p", "⊡(R ↔ □¬R ≺ □R) → ¬R", "□(□p ≺ □q) → □p ≺ □q",
                               "((□□Π ∧ ¬□Π) → Π) ∧ (Π → □Π) → □Π", "¬(□p ≺ □q) → □(□p → □q) ∨ □p ≺ □q"])
def test_lean(decider, A):
    """The Lean term of a model is one that Lean reads, and the model it reads is the one it
    is the term of: Lean, having read it, prints it again."""
    for model in decider.models_lean(A):
        assert decider._eval(f"Tableau.model ({model})") == model


def test_model_tex(decider):
    """The worlds are numbered from the first, each before the worlds below it; the boxed
    formulas of the orders are named where the worlds are and spelled out below them, with
    `≺` between those witnessed one before another and `≈` between those witnessed together;
    and only what first holds at a world is in its order."""
    tex = decider.model_tex('{ sees := [{ letters := ["φ", "q"], sees := [{}] }, { order := [["□φ"], ["□q", "□r"], ["□⊤"]] }] }')
    assert tex.startswith(r"\begin{forest}") and tex.endswith(r"\end{forest}")
    assert test_gl.worlds(tex) == [
        r"  [{$w_{0}$\nodepart{two}}",
        r"    [{$w_{1}$\nodepart{two}$\Vdash \ensuremath{\varphi}, q$}",
        r"      [{$w_{2}$\nodepart{two}}]]",
        r"    [{$w_{3}$\nodepart{two}$\Vdash b_{1} \prec b_{2} \approx b_{3}$}]]"]
    assert r"{$b_{1} = \Box \ensuremath{\varphi}$}" in tex and r"{$b_{3} = \Box r$}" in tex and "b_{4}" not in tex
