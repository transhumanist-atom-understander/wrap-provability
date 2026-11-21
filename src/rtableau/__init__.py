"""Witness comparison tableaux, built by Lean.

    with Decider(decider) as d:
        d.closed("⊡(Π ↔ □□Π ≺ □Π) → □Π")         # whether its tableau closes, so it is a theorem of R⁻
        d.tex("⊡(Π ↔ □□Π ≺ □Π) → □Π")            # the tableau as a LaTeX prooftree
        d.sentence_tex("⊡(Π ↔ □□Π ≺ □Π) → □Π")   # the sentence in LaTeX
        d.models_tex("□p → p")                    # the models of its open branches as LaTeX trees
        d.lean("□p → p")                          # the tableau as a Lean file

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
    spoken to until the `with` block ends. It imports the project's library, `RTableau`, once,
    at the start, and each request is evaluated where that left it. The REPL is the project's
    own executable, which has the library compiled in: the Lean it evaluates is interpreted,
    but what that calls of the library is not.

    A tableau is spoken of by its sentence, and nothing is kept of it: Lean builds it for each
    thing that is asked of it, which takes a small part of the time the request does. A
    sentence letter is any run of characters other than whitespace, parentheses and the
    connectives, `¬ □ ◇ ⊡` bind tightest, then `≺` and `≼`, which compare boxed formulas, then
    `∧`, `∨`, `→`, `↔`, each associating to the right. Each method raises `ValueError` if its
    sentence doesn't parse."""

    def __init__(self, project):
        lean = LocalProject(directory=project, auto_build=False)
        try:
            lean.build(verbose=False)
        except subprocess.CalledProcessError:
            raise LeanError(f"`lake build` in {project} failed: run it there to see why") from None
        super().__init__(LeanREPLConfig(project=lean, local_repl_path=Path(project), build_repl=False))
        self._library = self._run("import RTableau").env

    def _run(self, source, env=None):
        """Lean's reply to the Lean file `source`, or to `source` where the reply with the
        environment `env` left off; raises `LeanError` with Lean's errors."""
        reply = self.run(Command(cmd=source, env=env))
        if isinstance(reply, REPLError):
            raise LeanError(reply.message)
        if errors := reply.get_errors():
            raise LeanError("\n".join(m.data for m in errors))
        return reply

    def _eval(self, command):
        """What `#eval command` prints, where `command` is of a sentence; raises `ValueError`
        with the parse error if the sentence doesn't parse."""
        try:
            reply = self._run(f"#eval {command}", self._library)
        except LeanError as e:
            raise ValueError(str(e)) from None
        return "".join(m.data for m in reply.messages if m.severity == "info")

    def _decide(self, sentence, show):
        """What the Lean function `show` makes of the tableau for `sentence`, which Lean builds
        for it. Lean prints it as a string literal, which is on one line: the REPL takes time
        that is quadratic in the lines of what is printed, minutes for a tableau of 100,000."""
        literal = self._eval(f"Tableau.decide {json.dumps(sentence, ensure_ascii=False)} (String.quote ∘ {show})")
        escapes = {"n": "\n", "t": "\t"}
        return re.sub(r"\\(x[0-9a-f]{2}|.)", lambda m: chr(int(m[1][1:], 16)) if len(m[1]) == 3 else escapes.get(m[1], m[1]), literal[1:-1]).strip()

    def _letters(self, sentence):
        """The sentence letters of `sentence`, as Lean gives them, with their Greek letters and
        other such characters as LaTeX commands, for math mode: what goes in the fields of the
        format strings that Lean gives LaTeX as. Only the letters are turned into LaTeX here."""
        letters = self._eval(f"Tableau.letters {json.dumps(sentence, ensure_ascii=False)}").split(" ")
        return [re.sub(r"\\ensuremath\{([^{}]*)\}", r"\1", unicode_to_latex(a, non_ascii_only=True)) for a in letters]

    def _tex(self, sentence, show):
        """The LaTeX that the Lean function `show` makes of the tableau for `sentence`, in a
        LaTeX style, with its sentence letters as `_letters` has them."""
        return self._decide(sentence, f"(·.format {show})").format(*self._letters(sentence))

    def closed(self, sentence):
        """Whether the tableau for `sentence` closes: the sentence is a theorem of R⁻, and of
        GL if it has no comparison, if it does, and not a theorem if it doesn't."""
        return self._decide(sentence, "(toString ·.tree.isClosed)") == "true"

    def tex(self, sentence):
        """The tableau for `sentence` as a `prooftree` of the LaTeX package `prooftrees`."""
        return self._tex(sentence, "(fun t s => t.tex s)")

    def sentence_tex(self, sentence):
        """`sentence` in LaTeX, for math mode. No tableau is built for it."""
        return self._eval(f"Tableau.sentenceTex {json.dumps(sentence, ensure_ascii=False)}").format(*self._letters(sentence))

    def models_tex(self, sentence):
        """The models that the open branches of the tableau for `sentence` describe, each as a
        tree of the LaTeX package `forest`, which also needs the package `amssymb` and the TikZ
        library `shapes.multipart`: a list, the branches from left to right, with one model for branches that are drawn the same, and
        empty if the tableau closes. The worlds are drawn as a tree, with an arrow from each to
        the worlds started from it, and stand for the transitive order that generates; by each
        is what the branch says there of the sentence letters and the comparisons, which are
        named `c₁`, `c₂` and so on there and spelled out below the worlds. Each is a
        countermodel, a model of R⁻, however the letters that a world says nothing of are valued
        there; the comparisons it says nothing of are settled by how the boxed formulas came to
        hold on the way down to it."""
        printed = self._tex(sentence, '(fun t s => "\\n".intercalate (t.modelsTex s))')
        return [model.strip() for model in printed.split("\n\n") if model.strip()]

    def lean(self, sentence):
        """The tableau for `sentence` as a Lean file, which defines it as `t` and says, above
        it, what it shows: a record of the tableau, for a reader or for Lean. Lean is much
        slower to read it than to build the tableau, so nothing here does."""
        return self._decide(sentence, "Tableau.lean")
