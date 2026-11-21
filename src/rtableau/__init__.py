"""Witness comparison tableaux, built by Lean.

    with Decider(decider) as d:
        t = d.tableau("⊡(Π ↔ □□Π ≺ □Π) → □Π")   # the tableau as a Lean file
        d.closed(t)                              # whether it closed, so the sentence is a theorem of R⁻
        d.tex(t)                                 # the tableau as a LaTeX prooftree
        d.sentence_tex(t)                        # the sentence in LaTeX
        d.models_tex(d.tableau("□p → p"))        # the models of its open branches as LaTeX tikzpictures

The sentences are those of Guaspari and Solovay's R⁻: GL's, with the witness comparisons
`□A ≺ □B` and `□A ≼ □B`. The rules for comparisons are complete for R⁻, so a tableau closes if
its sentence is a theorem of R⁻ and doesn't if it is not; for a sentence of GL the tableau is
GL's.

`decider` is the directory of a checkout of the Lean project `decide-provability`; there is no
default, it must be given. A `Decider` builds the project, with `lake build`, and runs the Lean
REPL that the project builds in it, through `lean-interact`, with the project's library
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
    library, `RTableau`, which the REPL loads once, at the start, and reuses. The REPL is the
    project's own executable, which has the library compiled in: the Lean it evaluates is
    interpreted, but what that calls of the library is not."""

    def __init__(self, project):
        lean = LocalProject(directory=project, auto_build=False)
        try:
            lean.build(verbose=False)
        except subprocess.CalledProcessError:
            raise LeanError(f"`lake build` in {project} failed: run it there to see why") from None
        super().__init__(LeanREPLConfig(project=lean, local_repl_path=Path(project), build_repl=False))
        self._sentences = {}
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

    def _print(self, tableau, value):
        """What Lean prints for `value`, an expression in `t`, the tableau of the Lean file
        `tableau`. Lean builds a tableau much faster than it reads the file of one, so a
        tableau that this decider built is built again, from its sentence, and only another is
        read from its file."""
        if tableau in self._sentences:
            return self._run(f"import RTableau\n#eval do let t ← Tableau.ofSentence {self._sentences[tableau]}; IO.print ({value})")
        return self._run(f"{tableau}\n#eval IO.print ({value})")

    def _tex(self, tableau, value):
        """`_print`, with the Greek letters and other such characters of what it prints as
        LaTeX commands, for math mode."""
        tex = unicode_to_latex(self._print(tableau, value), non_ascii_only=True)
        return re.sub(r"\\ensuremath\{([^{}]*)\}", r"\1", tex)

    def tableau(self, sentence):
        """The tableau for `sentence`, where a sentence letter is any run of characters other
        than whitespace, parentheses and the connectives, `¬ □ ◇ ⊡` bind tightest, then `≺` and
        `≼`, which compare boxed formulas, then `∧`, `∨`, `→`, `↔`, each associating to the
        right: a Lean file defining it as `t`."""
        quoted = json.dumps(sentence, ensure_ascii=False)
        try:
            tableau = self._run(f"import RTableau\n#eval Tableau.decide {quoted}")
        except LeanError as e:
            raise ValueError(str(e)) from None
        self._sentences[tableau] = quoted
        return tableau

    def closed(self, tableau):
        """Whether the tableau of the Lean file `tableau` closed: its sentence is a theorem of
        R⁻, and of GL if it has no comparison, if it did, and not a theorem if it didn't."""
        return self._print(tableau, "t.tree.isClosed") == "true"

    def tex(self, tableau):
        """The tableau of the Lean file `tableau` as a `prooftree` of the LaTeX package
        `prooftrees`."""
        return self._tex(tableau, "t.tex")

    def sentence_tex(self, tableau):
        """The sentence of the Lean file `tableau` in LaTeX, for math mode."""
        return self._tex(tableau, "t.sentence.render .tex")

    def models_tex(self, tableau):
        """The models that the open branches of the tableau of the Lean file `tableau`
        describe, each as a `tikzpicture` of the LaTeX package `tikz`, which also needs
        `amssymb`: a list, the branches from left to right, with one model for branches that
        are drawn the same, and empty if the tableau closed. The worlds are drawn as a tree, with an arrow from each
        to the worlds started from it, and stand for the transitive order that generates; by
        each is what the branch says there of the sentence letters and the comparisons, which
        are named `c₁`, `c₂` and so on there and spelled out below the worlds. Each is a
        countermodel, a model of R⁻, however the letters that a world says nothing of are valued
        there; the comparisons it says nothing of are settled by how the boxed formulas came to
        hold on the way down to it."""
        printed = self._tex(tableau, '"\\n".intercalate t.modelsTex')
        return [model.strip() for model in printed.split("\n\n") if model.strip()]
