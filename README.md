# gltableau

A Python wrapper of [`gl-tableau`](../gl-tableau): tableaux for sentences of GL
(Gödel–Löb provability logic), checked by Lean with `ProvabilityLogic`.

```python
from gltableau import Decider

with Decider() as d:
    t = d.tableau("□(□p → p) → □p")   # the tableau as a Lean file
    d.closed(t)                       # True: it closed, so the sentence is a theorem of GL
    print(d.tex(t))                   # the tableau as a prooftree of the LaTeX package prooftrees
    print(d.sentence_tex(t))          # the sentence in LaTeX
    print(d.verify(t))                # the Lean file with a proof of its verdict, checked by Lean
```

A `Decider` starts the `tableau` server of the Lean project and talks to it until the `with`
block ends. Starting takes a couple of seconds, to load the Lean library (most of it Mathlib);
after that each request takes a fraction of a second, so decide many sentences in one `with`.
`verify` raises `LeanError`, with Lean's messages, if Lean rejects the proof, and `tableau`
raises `ValueError` if the sentence doesn't parse.

The same three functions are commands:

    $ gl-tableau tableau '□(□p → p) → □p' > lob.lean    # exit status 1 if the tableau is open
    $ gl-tableau tex lob.lean > lob.tex
    $ gl-tableau verify lob.lean

Run them from this directory with `uv run gl-tableau ...`, from anywhere with
`uvx --from /path/to/wrap-tableau gl-tableau ...`, or after `uv tool install /path/to/wrap-tableau`
just as `gl-tableau ...`.

## Setup

The Lean project is looked for at `$GL_TABLEAU`, or by default at `../gl-tableau` beside this
checkout. It must be built (see its README); `lake exe tableau` is run in it, so `lake` must
be on the path, as elan installs it.
