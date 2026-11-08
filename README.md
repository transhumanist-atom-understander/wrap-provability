# gltableau

A Python wrapper of
[decide-provability](https://github.com/transhumanist-atom-understander/decide-provability)
and
[verify-provability](https://github.com/transhumanist-atom-understander/verify-provability):
tableaux for sentences of GL (Gödel–Löb provability logic), and Lean's check of what they
show, with `ProvabilityLogic`.

```python
from gltableau import Decider, Verifier

with Decider("/path/to/decide-provability") as d:
    t = d.tableau("□(□p → p) → □p")   # the tableau as a Lean file
    d.closed(t)                       # True: it closed, so the sentence is a theorem of GL
    print(d.tex(t))                   # the tableau as a prooftree of the LaTeX package prooftrees
    print(d.sentence_tex(t))          # the sentence in LaTeX

with Verifier("/path/to/verify-provability") as v:
    print(v.verify(t))                # the Lean file with a proof of its verdict, checked by Lean
```

A `Decider` starts the `tableau` server of the decider and talks to it until the `with` block
ends; a `Verifier` does the same with the `verify` server of the verifier. Each is given the
directory of a checkout of its Lean project, which it builds, with `lake build`, if it is not
built: there is no default. The decider starts in a fraction of a second once built; the
verifier takes a couple of seconds to load its Lean library, most of it Mathlib, so verify many
tableaux in one `with`. `tableau` raises `ValueError` if the
sentence doesn't parse, and `verify` raises `LeanError`, with Lean's messages, if Lean rejects
the proof.

The same functions are commands, which find the Lean projects at `$GL_DECIDER` and
`$GL_VERIFIER` and fail if the one they need is not set:

    $ export GL_DECIDER=/path/to/decide-provability GL_VERIFIER=/path/to/verify-provability
    $ gl-tableau tableau '□(□p → p) → □p' > lob.lean    # exit status 1 if the tableau is open
    $ gl-tableau tex lob.lean > lob.tex
    $ gl-tableau verify lob.lean

Run them from this directory with `uv run gl-tableau ...`, from anywhere with
`uvx --from /path/to/wrap-provability gl-tableau ...`, or after
`uv tool install /path/to/wrap-provability` just as `gl-tableau ...`.

## Setup

Check out the decider, and the verifier if you want to verify, and for the verifier fetch
Mathlib's prebuilt artifacts as its README says: it is the one that needs Mathlib. `lake` is run
in their directories, so it must be on the path, as elan installs it.
