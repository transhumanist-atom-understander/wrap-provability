"""The timeout of a `Decider`: Lean is stopped when a request takes longer, and the `Decider`
is as it was.

The sentence is of a program that plays a prisoner's dilemma by which of two proofs it finds
first: it says that the program cooperates or defects, if no two of its searches end
together. It is not a theorem, since a search may not end, and its tableau takes much longer
than the second it is given here.
"""

import os

import pytest

from rtableau import Decider

A, B, C, D = "□(C₁ → C₂)", "□(C₁ → D₂)", "□(D₁ → D₂)", "□(D₁ → C₂)"
PROGRAM = (
    f"⊡((C₁ ↔ {A} ≺ {B} ∧ {C} ≺ {D})"
    f" ∧ (D₁ ↔ {A} ≺ {B} ∧ {D} ≺ {C} ∨ {B} ≺ {A} ∧ {C} ≺ {D} ∨ {B} ≺ {A} ∧ {D} ≺ {C}))"
)
NO_TIES = f"⊡(¬({A} ≼ {B} ∧ {B} ≼ {A}) ∧ ¬({C} ≼ {D} ∧ {D} ≼ {C}))"
SLOW = f"{PROGRAM} ∧ {NO_TIES} → C₁ ∨ D₁"
HANGS = f"""{{ order := [["{C}"], ["{D}"]], sees := [
  {{ letters := ["C₁"], order := [["{A}"], ["{B}"], ["{C}"], ["{D}"]] }} ] }}"""


def test_timeout():
    if "DECIDE_PROVABILITY" not in os.environ:
        pytest.skip("$DECIDE_PROVABILITY is not set to a checkout of the Lean project")
    with Decider(os.environ["DECIDE_PROVABILITY"], timeout=1) as d:
        assert d.closed("□(□p → p) → □p")
        with pytest.raises(TimeoutError):
            d.closed(SLOW)
        assert d.closed("□(□p → p) → □p")
        assert not d.closed("□p → p")
        with pytest.raises(TimeoutError):
            d.models_lean(SLOW)
        assert d.models_lean("□p → p") == ["{}"]
        # A model written by hand settles it, with no tableau: at its first world the searches
        # for what follows from cooperating don't end, so the program does neither.
        assert not d.satisfied(SLOW, HANGS)
