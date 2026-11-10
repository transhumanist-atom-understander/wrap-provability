# tableau

A Python wrapper of
[decide-provability](https://github.com/transhumanist-atom-understander/decide-provability)
and
[verify-provability](https://github.com/transhumanist-atom-understander/verify-provability):
tableaux for sentences of provability logics, and Lean's check of what they show, with
`ProvabilityLogic`. There are two logics, each a module: `tableau.gl` is GL (Gödel–Löb
provability logic), and `tableau.rminus` is R⁻, Guaspari and Solovay's GL with the witness
comparisons `□A ≺ □B` and `□A ≼ □B` of Rosser sentences.

```python
from tableau.gl import Decider, Verifier

with Decider("/path/to/decide-provability") as d:
    t = d.tableau("□(□p → p) → □p")   # the tableau as a Lean file
    d.closed(t)                       # True: it closed, so the sentence is a theorem of GL
    print(d.tex(t))                   # the tableau as a prooftree of the LaTeX package prooftrees
    print(d.sentence_tex(t))          # the sentence in LaTeX

with Verifier("/path/to/verify-provability") as v:
    print(v.verify(t))                # the Lean file with a proof of its verdict, checked by Lean
```

```python
from tableau.rminus import Decider

with Decider("/path/to/decide-provability") as d:
    t = d.tableau("□(□⊤ ≺ □⊥)")       # the same, for R⁻
    d.closed(t)                       # True: it is a theorem of R⁻, though □⊤ ≺ □⊥ is not
```

A `Decider` runs the [Lean REPL](https://github.com/augustepoiroux/repl) in the decider's
project, with the library of its logic imported, and talks to it until the `with` block ends;
a `Verifier` does the same in the verifier's project. Each is given the directory of a checkout
of its Lean project, which it builds, with `lake build`, if it is not built: there is no
default. Both deciders are given the same checkout. The decider's REPL starts in a second once
built; the verifier's takes a couple of seconds to import its library, most of it Mathlib, so
verify many tableaux in one `with`. A sentence letter is any run of characters other than
whitespace, parentheses and the connectives, and `tex` and `sentence_tex` print its Greek
letters and other such characters as LaTeX commands, `φ` as `\varphi`, with `pylatexenc`.
`tableau` raises `ValueError` if the sentence doesn't parse, and `verify` raises `LeanError`,
with Lean's messages, if Lean rejects the proof.

In a sentence of R⁻, `≺` and `≼` bind tighter than `∧` and looser than `¬ □ ◇ ⊡`, and what they
compare must be written as boxed formulas: `□p ≺ □q ∧ r` is `(□p ≺ □q) ∧ r`, and `¬□p ≺ □q`
doesn't parse, but `¬(□p ≺ □q)` does. There is no verifier of R⁻ tableaux yet.

The same functions are commands, one for each logic, which find the Lean projects at
`$GL_DECIDER` and `$GL_VERIFIER` and fail if the one they need is not set:

    $ export GL_DECIDER=/path/to/decide-provability GL_VERIFIER=/path/to/verify-provability
    $ gl-tableau tableau '□(□p → p) → □p' > lob.lean    # exit status 1 if the tableau is open
    $ gl-tableau tex lob.lean > lob.tex
    $ gl-tableau verify lob.lean
    $ rminus-tableau tableau '□(□⊤ ≺ □⊥)' > first.lean  # exit status 1 if the tableau is open
    $ rminus-tableau tex first.lean > first.tex

Run them from this directory with `uv run gl-tableau ...`, from anywhere with
`uvx --from /path/to/wrap-provability gl-tableau ...`, or after
`uv tool install /path/to/wrap-provability` just as `gl-tableau ...`.

## Setup

Check out the decider, and the verifier if you want to verify: it is the one that needs
Mathlib. Each requires the REPL as a Lake dependency, at the tag for its toolchain, so it is
fetched and built with the project and nothing is fetched from Python;
[`lean-interact`](https://github.com/augustepoiroux/LeanInteract) is pointed at that checkout.
`lake` is run in the projects' directories, so it must be on the path, as elan installs it.

## Tests

The tests are the project's, not the wrapper's alone: they have the decider build tableaux for
theorems and non-theorems of GL and the verifier check them, so a sentence can be added without
knowing its verdict. They find the Lean projects as the commands do, and skip what needs one
that isn't set:

    $ GL_DECIDER=/path/to/decide-provability GL_VERIFIER=/path/to/verify-provability uv run pytest

The tableaux for R⁻ have no verifier to check them. In its place, `tests/rminus_models.py`
decides each sentence of `tests/test_rminus.py` again from Guaspari and Solovay's models of
R⁻, by brute force, and the tests have the two agree; they also have the R⁻ decider agree with
GL's on the sentences of GL. The search is exponential in the number of boxed subformulas, so
it is for small sentences.
