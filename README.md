# gltableau

A Python wrapper of
[decide-provability](https://github.com/transhumanist-atom-understander/decide-provability):
tableaux for sentences of GL (Gödel–Löb provability logic).

```python
from gltableau import Decider

with Decider("/path/to/decide-provability") as d:
    t = d.tableau("□(□p → p) → □p")   # the tableau as a Lean file
    d.closed(t)                       # True: it closed, so the sentence is a theorem of GL
    print(d.tex(t))                   # the tableau as a prooftree of the LaTeX package prooftrees
    print(d.sentence_tex(t))          # the sentence in LaTeX
```

A `Decider` runs the [Lean REPL](https://github.com/augustepoiroux/repl) in the decider's
project, with its library imported, and talks to it until the `with` block ends. It is given
the directory of a checkout of that Lean project, which it builds, with `lake build`, if it is
not built: there is no default. The REPL starts in a second once built. A sentence letter is
any run of characters other than whitespace, parentheses and the connectives, and `tex` and
`sentence_tex` print its Greek letters and other such characters as LaTeX commands, `φ` as
`\varphi`, with `pylatexenc`. `tableau` raises `ValueError` if the sentence doesn't parse.

The same functions are commands, which find the Lean project at `$GL_DECIDER` and fail if it is
not set:

    $ export GL_DECIDER=/path/to/decide-provability
    $ gl-tableau tableau '□(□p → p) → □p' > lob.lean    # exit status 1 if the tableau is open
    $ gl-tableau tex lob.lean > lob.tex

Run them from this directory with `uv run gl-tableau ...`, from anywhere with
`uvx --from /path/to/wrap-provability gl-tableau ...`, or after
`uv tool install /path/to/wrap-provability` just as `gl-tableau ...`.

## Setup

Check out the decider. It requires the REPL as a Lake dependency, at the tag for its toolchain,
so it is fetched and built with the project and nothing is fetched from Python;
[`lean-interact`](https://github.com/augustepoiroux/LeanInteract) is pointed at that checkout.
`lake` is run in the project's directory, so it must be on the path, as elan installs it.

## Tests

The tests are the project's, not the wrapper's alone: they have the decider build tableaux for
theorems and non-theorems of GL and check that each closes or doesn't, so a sentence is added
with its verdict. They find the Lean project as the commands do, and are skipped if it isn't
set:

    $ GL_DECIDER=/path/to/decide-provability uv run pytest
