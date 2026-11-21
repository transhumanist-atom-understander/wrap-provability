# rtableau

A Python wrapper of
[decide-provability](https://github.com/transhumanist-atom-understander/decide-provability):
tableaux for sentences with witness comparisons, those of Guaspari and Solovay's R⁻, the logic
of Rosser sentences, which is GL (Gödel–Löb provability logic) with `□A ≺ □B` and `□A ≼ □B`.

```python
from rtableau import Decider

with Decider("/path/to/decide-provability") as d:
    parikh = "⊡(Π ↔ □□Π ≺ □Π) → □Π"   # the Parikh sentence is provably provable
    d.closed(parikh)                   # True: its tableau closes, so it is a theorem of R⁻
    print(d.tex(parikh))               # the tableau as a prooftree of the LaTeX package prooftrees
    print(d.sentence_tex(parikh))      # the sentence in LaTeX
    print(d.lean(parikh))              # the tableau as a Lean file
```

A tableau is spoken of by its sentence. Nothing is kept of it: Lean builds it for each thing
that is asked of it, in well under a millisecond for a sentence like these, where the request
itself takes a few milliseconds.

A tableau that doesn't close has open branches, and `models_tex` draws the model each describes,
as a list, from the leftmost branch to the rightmost, with one model for branches that are
drawn the same. The list is empty if the tableau closes.

```python
    for model in d.models_tex("□p → p"):   # LaTeX trees: here, one
        print(model)
```

    \begin{forest}
      for tree={rectangle split, rectangle split horizontal, rectangle split parts=2, inner sep=2pt,
        anchor=text, parent anchor=one south, child anchor=one north, l=12mm, l sep=0pt, s sep=5mm,
        edge={->, >=stealth}}
      [{$w_{0}$\nodepart{two}$\Vdash \lnot p$}]
    \end{forest}

Each can be pasted into the body of a document that has `\usepackage{forest}`,
`\usepackage{amssymb}` and `\usetikzlibrary{shapes.multipart}`, as the `prooftree` of `tex` can
into one with `\usepackage{prooftrees}`, which loads `forest` itself. It is `forest` that puts
the worlds where they go, from the sizes of what is typeset by them, so a letter takes the room
that it does in print, however it was typed.
The worlds are drawn as a tree, an arrow from each to the worlds started from it, and stand for
the transitive order that generates. By each world is what the branch says there of the
sentence letters and the comparisons; a letter it says nothing of can be valued either way.
The comparisons are long, so they are named `c₁`, `c₂` and so on where the worlds are, and
spelled out below them, which keeps the drawing narrow enough for a page. Of
a sentence of GL each is a countermodel, and of a sentence with comparisons too, a model of
R⁻: the comparisons a world says nothing of are settled by how the boxed formulas came to hold
on the way down to it.

The rules for comparisons are complete for R⁻, as
[the decider's README](https://github.com/transhumanist-atom-understander/decide-provability#witness-comparisons)
sets out: a tableau closes if its sentence is a theorem of R⁻ and doesn't if it is not. A
comparison that fails is traded for its converse, a comparison that holds is traced back to the
world where it came to hold, and a branch also closes on comparisons at a world that go round
in a circle, one of them strict. For a sentence of GL, one with no comparison, the tableau is
GL's.

```python
with Decider("/path/to/decide-provability") as d:
    d.closed("□p ≺ □q ∧ □q ≺ □r → □p ≺ □r")   # True: a theorem of R⁻
    d.closed("□⊤ ≺ □⊥")                       # False: not a theorem of R⁻
```

```python
with Decider("/path/to/decide-provability") as d:
    d.closed("□(□p → p) → □p")   # True: a theorem of GL
    d.closed("□p → p")           # False: not a theorem of GL
```

The Lean file that `lean` gives defines the tableau, as `t`, and says above it which of these it
shows. It is a record of the tableau, for a reader or for Lean, in the decider's project; Lean
is much slower to read it than to build the tableau, so the wrapper has no use for it.

A `Decider` runs the [Lean REPL](https://github.com/augustepoiroux/repl) in the decider's
project, with its library imported, and talks to it until the `with` block ends. It is given
the directory of a checkout of that Lean project, which it builds, with `lake build`, if it is
not built: there is no default. The REPL starts in a second once built. A sentence letter is
any run of characters other than whitespace, parentheses and the connectives, and `tex`,
`sentence_tex` and `models_tex` print its Greek letters and other such characters as LaTeX
commands, `φ` as `\varphi`, with `pylatexenc`; a letter can be LaTeX to begin with, `\varphi`
or `p_{1}`, and is printed as it is. Lean gives the sentence letters, and the LaTeX as a format
string with a field for each, so only the letters are turned into LaTeX, and the rest is as
Lean has it. `¬ □ ◇ ⊡` bind tightest, then `≺` and `≼`, then `∧`, `∨`, `→`,
`↔`, and what `≺` and `≼` compare must be written as boxed formulas: `□p ≺ □q ∧ r` is
`(□p ≺ □q) ∧ r`, and `¬□p ≺ □q` doesn't parse, but `¬(□p ≺ □q)` does. Each method raises
`ValueError` if its sentence doesn't parse.

## Setup

Check out the decider. It requires the REPL as a Lake dependency, at the tag for its toolchain,
and builds it as an executable of its own, with the library compiled in, so it is fetched and
built with the project and nothing is fetched from Python;
[`lean-interact`](https://github.com/augustepoiroux/LeanInteract) is pointed at that checkout.
`lake` is run in the project's directory, so it must be on the path, as elan installs it.

## Tests

The tests are the project's, not the wrapper's alone. They find the Lean project at
`$DECIDE_PROVABILITY`, and are skipped if it isn't set:

    $ DECIDE_PROVABILITY=/path/to/decide-provability uv run pytest

`tests/test_gl.py` has the decider build tableaux for theorems and non-theorems of GL and checks
that each closes or doesn't, so a sentence is added with its verdict.

`tests/test_witness.py` does the same for sentences with comparisons, theorems of R⁻ and
non-theorems, and checks the tableaux with `tests/witness_semantics.py`, which decides each of
its sentences again from Guaspari and Solovay's models of R⁻, by brute force, and sentences at
random too: the two must agree. That search is exponential, so it is for small sentences. It
also has Lean read the Lean files of some tableaux and print them again, which must give the
file: nothing else reads one.
