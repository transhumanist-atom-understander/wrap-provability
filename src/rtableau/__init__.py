"""Witness comparison tableaux, built by Lean.

    with Decider(decider) as d:
        t = d.tableau("⊡(Π ↔ □□Π ≺ □Π) → □Π")   # the tableau as a Lean file
        d.closed(t)                              # whether it closed, so the sentence is a theorem of R⁻
        d.tex(t)                                 # the tableau as a LaTeX prooftree
        d.sentence_tex(t)                        # the sentence in LaTeX
        d.model_tex(d.tableau("□p → p"))         # the model of an open branch as a LaTeX tikzpicture

The sentences are those of Guaspari and Solovay's R⁻: GL's, with the witness comparisons
`□A ≺ □B` and `□A ≼ □B`. The rules for comparisons are not all of R⁻ yet, so a tableau that
closes shows a theorem of R⁻ but one that doesn't shows a non-theorem only if its sentence has
no comparison: for a sentence of GL the tableau is GL's, and decides it.

`decider` is the directory of a checkout of the Lean project `decide-provability`; there is no
default, it must be given. A `Decider` builds the project, with `lake build`, and runs the Lean
REPL that the project requires in it, through `lean-interact`, with the project's library
imported; after that every request is fast.
"""

import json
import re
import subprocess
from pathlib import Path

from lean_interact import Command, LeanREPLConfig, LeanServer, LocalProject
from lean_interact.interface import LeanError as REPLError
from pylatexenc.latexencode import unicode_to_latex


class LeanError(Exception):
    """Lean rejected the source: the message is its errors."""


class Decider(LeanServer):
    """The Lean REPL run in `decide-provability`, at `project`, after `lake build` there, and
    spoken to until the `with` block ends. Each request is a Lean file importing the project's
    library, `RTableau`, which the REPL loads once, at the start, and reuses."""

    def __init__(self, project):
        lean = LocalProject(directory=project, auto_build=False)
        try:
            lean.build(verbose=False)
        except subprocess.CalledProcessError:
            raise LeanError(f"`lake build` in {project} failed: run it there to see why") from None
        super().__init__(LeanREPLConfig(project=lean, local_repl_path=Path(project, ".lake/packages/REPL")))
        self._run("import RTableau")

    def _run(self, source):
        """What the `#eval`s of the Lean file `source` print; raises `LeanError` with Lean's
        errors."""
        reply = self.run(Command(cmd=source))
        if isinstance(reply, REPLError):
            raise LeanError(reply.message)
        if errors := reply.get_errors():
            raise LeanError("\n".join(m.data for m in errors))
        return "".join(m.data for m in reply.messages if m.severity == "info")

    def _tex(self, source):
        """`_run`, with the Greek letters and other such characters of what it prints as LaTeX
        commands, for math mode."""
        tex = unicode_to_latex(self._run(source), non_ascii_only=True)
        return re.sub(r"\\ensuremath\{([^{}]*)\}", r"\1", tex)

    def tableau(self, sentence):
        """The tableau for `sentence`, where a sentence letter is any run of characters other
        than whitespace, parentheses and the connectives, `¬ □ ◇ ⊡` bind tightest, then `≺` and
        `≼`, which compare boxed formulas, then `∧`, `∨`, `→`, `↔`, each associating to the
        right: a Lean file defining it as `t`."""
        try:
            return self._run(f"import RTableau\n#eval Tableau.decide {json.dumps(sentence, ensure_ascii=False)}")
        except LeanError as e:
            raise ValueError(str(e)) from None

    def closed(self, tableau):
        """Whether the tableau of the Lean file `tableau` closed, so its sentence is a theorem
        of R⁻, and of GL if it has no comparison. If it didn't, a sentence with no comparison is
        not a theorem; of one with comparisons it only shows that persistence and true before
        false, the rules there are for them, are not enough."""
        return self._run(tableau + "\n#eval IO.print t.tree.isClosed") == "true"

    def tex(self, tableau):
        """The tableau of the Lean file `tableau` as a `prooftree` of the LaTeX package
        `prooftrees`."""
        return self._tex(tableau + "\n#eval IO.print t.tex")

    def sentence_tex(self, tableau):
        """The sentence of the Lean file `tableau` in LaTeX, for math mode."""
        return self._tex(tableau + "\n#eval IO.print (t.sentence.render .tex)")

    def model_tex(self, tableau):
        """The model that the first open branch of the tableau of the Lean file `tableau`
        describes, as a `tikzpicture` of the LaTeX package `tikz`, which also needs `amssymb`;
        `None` if the tableau closed. The worlds are drawn as a tree, with an arrow from each
        to the worlds started from it, and stand for the transitive order that generates; by
        each is what the branch says there of the sentence letters and the comparisons, which
        are named `c₁`, `c₂` and so on there and spelled out below the worlds. Of a
        sentence with no comparison it is a countermodel, however the letters that a world says
        nothing of are valued there; of one with comparisons it is a model of the rules there
        are for them, and not always one of R⁻."""
        return self._tex(tableau + '\n#eval IO.print (t.modelTex.getD "")') or None
