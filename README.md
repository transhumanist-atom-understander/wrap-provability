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
    d.models_lean("□p → p")            # ['{}']: the models of its open branches, as Lean terms
    d.satisfied("□p → p", "{}")        # False: the sentence fails in a model, so it is not a theorem
```

A tableau is spoken of by its sentence. Nothing is kept of it: Lean builds it for each thing
that is asked of it, in well under a millisecond for a sentence like these, where the request
itself takes a few milliseconds.

A tableau that doesn't close has open branches, and each describes a countermodel.
`models_lean` gives them as a list, from the leftmost branch to the rightmost, with one model
for branches that describe the same, and `models_tex` draws them, in that order. The list is
empty if the tableau closes.

```python
    for model in d.models_lean("□p ∧ □q → □(p ∧ q) ≼ □p"):   # Lean terms: here, one
        print(model)
    for model in d.models_tex("□p ∧ □q → □(p ∧ q) ≼ □p"):    # LaTeX trees: here, one
        print(model)
```

    { order := [["□p"], ["□(p ∧ q)"]] }
    \begin{forest}
      for tree={rectangle split, rectangle split horizontal, rectangle split parts=2, inner sep=2pt,
        anchor=text, parent anchor=one south, child anchor=one north, l=12mm, l sep=0pt, s sep=5mm,
        edge={->, >=stealth}}
      [{$w_{0}$\nodepart{two}$\Vdash b_{1} \prec b_{2}$}]
      \node[anchor=north, inner sep=0pt] at ([yshift=-3mm]current bounding box.south) {$b_{1} = \Box p$};
      \node[anchor=north, inner sep=0pt] at ([yshift=-3mm]current bounding box.south) {$b_{2} = \Box (p \land q)$};
    \end{forest}

A tree can be pasted into the body of a document that has `\usepackage{forest}`,
`\usepackage{amssymb}` and `\usetikzlibrary{shapes.multipart}`, as the `prooftree` of `tex` can
into one with `\usepackage{prooftrees}`, which loads `forest` itself. It is `forest` that puts
the worlds where they go, from the sizes of what is typeset by them, so a letter takes the room
that it does in print, however it was typed.
The worlds are drawn as a tree, an arrow from each to the worlds just below it, and stand for
the transitive order that generates. By each world is what holds there: its sentence letters,
and the order in which the boxed formulas that first hold there are witnessed, `≺` between
those witnessed one before the other and `≈` between those witnessed together. The boxed
formulas are long, so they are named `b₁`, `b₂` and so on where the worlds are, and spelled out
below them, which keeps the drawing narrow enough for a page.

## Models

A model is a Lean term, of the decider's type `Tableau.Model`: a world, and the worlds below it.

```python
    model = '''{ sees := [{ order := [["□p"], ["□q"]] },
                         { order := [["□q"], ["□p"]] }] }'''
    d.satisfied("◇(□p ≺ □q) ∧ ◇(□q ≺ □p)", model)      # True: it holds in the model
    d.satisfied("¬(◇(□p ≺ □q) ∧ ◇(□q ≺ □p))", model)   # False: so this is not a theorem of R⁻
    print(d.model_tex(model))                            # the model as a LaTeX tree
```

`letters` are the sentence letters that hold at a world, `sees` the worlds just below it, each
such a term, and `order` is for the boxed formulas that first hold at the world, written as in
a sentence: those of a list are witnessed together, before those of the next list, and those in
no list after them all, together. A field that is left out is empty, and `{}` is a world where
no letter holds, with no world below. The tree is read as the transitive order it generates: a
boxed formula holds at a world if its formula holds at every world below it, and is witnessed
at the world where it first holds, after those that held already at the world above; `□A ≺ □B`
holds at a world if `□A` holds there and `□B` doesn't, or was witnessed after it, and `□A ≼ □B`
if `□A` holds there and `□B` doesn't, or wasn't witnessed before it. So the model above has two
worlds below its first, where `□p` and `□q` first hold, in one order at one and the other at
the other.

Every such term is a model of R⁻, [as the decider's README
has it](https://github.com/transhumanist-atom-understander/decide-provability#models), so there
is nothing to check of a model but what holds in it: a sentence that is not `satisfied` by one
is not a theorem of R⁻. That needs no tableau, and takes a few milliseconds, so a model written
by hand shows a non-theorem whose tableau is too large to build: write the model, and ask
whether the sentence is satisfied by it. `satisfied` takes the sentence first, as every method
does, and the model second. `model_tex` turns the Lean term of a model into its LaTeX tree, and
`models_tex` gives what it makes of each of `models_lean`. Both raise `ValueError` if Lean
doesn't read the model, or if it has a letter that isn't one or something in an order that
isn't a boxed formula.

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
`sentence_tex`, `models_tex` and `model_tex` print its Greek letters and other such characters as LaTeX
commands, as `pylatexenc` gives them, `φ` as `\ensuremath{\varphi}`, which is `\varphi` in math
mode, whatever comes after it; a letter can be LaTeX to begin with, `\varphi` or `p_{1}`, and is
printed as it is. The LaTeX is for LaTeX to compile, not for MathJax or KaTeX. Lean gives the sentence letters, and the LaTeX as a format
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

`tests/test_models.py` is about models. It has the decider check each model that an open
tableau describes, for the non-theorems of both lists and for sentences at random: the sentence
must fail in it. It has it check the theorems of both lists in models at random, where each
must hold. And it has `tests/witness_semantics.py` work out again what holds in a model,
straight from what that means, for sentences and models at random: the two must agree.
