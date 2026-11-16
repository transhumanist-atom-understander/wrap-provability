# rtableau

A Python wrapper of
[decide-provability](https://github.com/transhumanist-atom-understander/decide-provability):
tableaux for sentences with witness comparisons, those of Guaspari and Solovay's R⁻, the logic
of Rosser sentences, which is GL (Gödel–Löb provability logic) with `□A ≺ □B` and `□A ≼ □B`.

```python
from rtableau import Decider

with Decider("/path/to/decide-provability") as d:
    t = d.tableau("⊡(Π ↔ □□Π ≺ □Π) → □Π")   # the tableau as a Lean file: the Parikh sentence is provably provable
    d.closed(t)                              # True: it closed, so the sentence is a theorem of R⁻
    print(d.tex(t))                          # the tableau as a prooftree of the LaTeX package prooftrees
    print(d.sentence_tex(t))                 # the sentence in LaTeX
```

A tableau that doesn't close has an open branch, and `model_tex` draws the model it describes:

```python
    print(d.model_tex(d.tableau("□p → p")))  # a LaTeX tikzpicture; None if the tableau closed
```

    \begin{tikzpicture}[>=stealth]
      \node[inner sep=2pt] (w0) at (0mm,0mm) {$w_{0}$};
      \node[anchor=west, inner sep=0pt] at (w0.east) {$\,\Vdash \lnot p$};
    \end{tikzpicture}

It can be pasted into the body of a document that has `\usepackage{tikz}` and
`\usepackage{amssymb}`, as the `prooftree` of `tex` can into one with `\usepackage{prooftrees}`.
The worlds are drawn as a tree, an arrow from each to the worlds started from it, and stand for
the transitive order that generates. By each world is what the branch says there of the
sentence letters and the comparisons; a letter it says nothing of can be valued either way. Of
a sentence of GL this is a countermodel. Of a sentence with comparisons it is a model of the
rules there are for them, and not always one of R⁻.

The rules for comparisons are not all of R⁻ yet. They are the persistence of a comparison and
that true comes before false, `(□A ∧ ¬□B) → □A ≺ □B`, as
[the decider's README](https://github.com/transhumanist-atom-understander/decide-provability#witness-comparisons)
sets out, in place of those axioms as premises. So a tableau that closes shows a theorem of R⁻,
but one that doesn't shows only that those rules are not enough: they say nothing of the order
of boxed formulas that come to hold together, so `□p ≺ □q → ¬(□q ≺ □p)` is not proved. A
sentence of GL, one with no comparison, is the special case that is decided: its tableau is
GL's, and closes if the sentence is a theorem of GL and doesn't if it is not.

```python
with Decider("/path/to/decide-provability") as d:
    d.closed(d.tableau("□(□p → p) → □p"))   # True: a theorem of GL
    d.closed(d.tableau("□p → p"))           # False: not a theorem of GL
```

The Lean file says, above its tableau, which of these it shows.

A `Decider` runs the [Lean REPL](https://github.com/augustepoiroux/repl) in the decider's
project, with its library imported, and talks to it until the `with` block ends. It is given
the directory of a checkout of that Lean project, which it builds, with `lake build`, if it is
not built: there is no default. The REPL starts in a second once built. A sentence letter is
any run of characters other than whitespace, parentheses and the connectives, and `tex` and
`sentence_tex` print its Greek letters and other such characters as LaTeX commands, `φ` as
`\varphi`, with `pylatexenc`. `¬ □ ◇ ⊡` bind tightest, then `≺` and `≼`, then `∧`, `∨`, `→`,
`↔`, and what `≺` and `≼` compare must be written as boxed formulas: `□p ≺ □q ∧ r` is
`(□p ≺ □q) ∧ r`, and `¬□p ≺ □q` doesn't parse, but `¬(□p ≺ □q)` does. `tableau` raises
`ValueError` if the sentence doesn't parse.

## Setup

Check out the decider. It requires the REPL as a Lake dependency, at the tag for its toolchain,
so it is fetched and built with the project and nothing is fetched from Python;
[`lean-interact`](https://github.com/augustepoiroux/LeanInteract) is pointed at that checkout.
`lake` is run in the project's directory, so it must be on the path, as elan installs it.

## Tests

The tests are the project's, not the wrapper's alone. They find the Lean project at
`$DECIDE_PROVABILITY`, and are skipped if it isn't set:

    $ DECIDE_PROVABILITY=/path/to/decide-provability uv run pytest

`tests/test_gl.py` has the decider build tableaux for theorems and non-theorems of GL and checks
that each closes or doesn't, so a sentence is added with its verdict.

`tests/test_witness.py` does the same for sentences with comparisons, listed as theorems of R⁻
whose tableau closes, theorems whose tableau doesn't, and non-theorems, and checks the tableaux
in two more ways, with `tests/witness_semantics.py`. It decides each of its sentences again
from Guaspari and Solovay's models of R⁻, by brute force, and sentences at random too: what the
decider proves must be a theorem. And it has the decider decide, as a sentence of GL, whether a
sentence follows from the axioms that the rules replace, taken as premises, which is how such a
tableau is drawn by hand: the two must agree. Both searches are exponential, so they are for
small sentences, and the second is only run on those listed there as small.
