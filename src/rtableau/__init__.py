"""Witness comparison tableaux, built by Lean.

    with Decider(decider) as d:
        d.closed("⊡(Π ↔ □□Π ≺ □Π) → □Π")         # whether its tableau closes, so it is a theorem of R⁻
        d.tex("⊡(Π ↔ □□Π ≺ □Π) → □Π")            # the tableau as a LaTeX prooftree
        d.sentence_tex("⊡(Π ↔ □□Π ≺ □Π) → □Π")   # the sentence in LaTeX
        d.models_tex("□p → p")                    # the models of its open branches as LaTeX trees
        d.models_lean("□p → p")                   # the same models as Lean terms
        d.lean("□p → p")                          # the tableau as a Lean file

        d.satisfied("□p → p", "{}")               # whether the sentence holds in a model: a Lean term
        d.model_tex("{}")                         # the model as a LaTeX tree

The sentences are those of Guaspari and Solovay's R⁻: GL's, with the witness comparisons
`□A ≺ □B` and `□A ≼ □B`. The rules for comparisons are complete for R⁻, so a tableau closes if
its sentence is a theorem of R⁻ and doesn't if it is not; for a sentence of GL the tableau is
GL's.

A model is a Lean term, of the decider's type `Tableau.Model`, and every such term is a model
of R⁻: so a sentence that is not `satisfied` by one is not a theorem, whether the model is one
that a tableau gave or one written by hand, and that check needs no tableau.

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


def _math(tex):
    """`tex`, a sentence letter as `pylatexenc` gives it, without its `\\ensuremath`s: each is
    its argument, with a space after it if that ends in a command and a letter comes next,
    which would otherwise be read as more of the command's name."""
    def bare(m):
        space = " " if re.search(r"\\[A-Za-z]+$", m[1]) and re.match(r"[A-Za-z]", tex[m.end():]) else ""
        return m[1] + space
    return re.sub(r"\\ensuremath\{((?:[^{}]|\{[^{}]*\})*)\}", bare, tex)


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
    sentence doesn't parse.

    `timeout` is how many seconds Lean is given for each thing that is asked of it, and by
    default it is given as long as it takes. A tableau can be very large, so with a timeout a
    method raises `TimeoutError` if Lean takes longer than that. The REPL is killed then, since
    there is no other way to stop it, and started again, which takes a second: the `Decider`
    is as it was, for the next request."""

    def __init__(self, project, timeout=1):
        self._timeout = timeout
        lean = LocalProject(directory=project, auto_build=False)
        try:
            lean.build(verbose=False)
        except subprocess.CalledProcessError:
            raise LeanError(f"`lake build` in {project} failed: run it there to see why") from None
        super().__init__(LeanREPLConfig(project=lean, local_repl_path=Path(project), build_repl=False))
        self._library = self._run("import RTableau").env

    def _run(self, source, env=None, timeout=None):
        """Lean's reply to the Lean file `source`, or to `source` where the reply with the
        environment `env` left off; raises `LeanError` with Lean's errors. Lean is given
        `timeout` seconds for it, if that is not `None`: past that `lean-interact` kills the
        REPL, so it is started again here, with the library imported, and `TimeoutError` is
        raised."""
        try:
            reply = self.run(Command(cmd=source, env=env), timeout=timeout)
        except TimeoutError:
            self.start()
            self._library = self._run("import RTableau").env
            raise TimeoutError(f"Lean took more than {timeout} seconds, and was stopped") from None
        if isinstance(reply, REPLError):
            raise LeanError(reply.message)
        if errors := reply.get_errors():
            raise LeanError("\n".join(m.data for m in errors))
        return reply

    def _eval(self, command):
        """What `#eval command` prints, where `command` is of a sentence; raises `ValueError`
        with the parse error if the sentence doesn't parse, and `TimeoutError` if Lean takes
        longer than the timeout."""
        try:
            reply = self._run(f"#eval {command}", self._library, self._timeout)
        except LeanError as e:
            raise ValueError(str(e)) from None
        return "".join(m.data for m in reply.messages if m.severity == "info")

    def _printed(self, command):
        """What `command` prints, where it prints a string literal that Lean has quoted, which
        is on one line: the REPL takes time that is quadratic in the lines of what is printed,
        minutes for a tableau of 100,000."""
        escapes = {"n": "\n", "t": "\t"}
        literal = self._eval(command)
        return re.sub(r"\\(x[0-9a-f]{2}|.)", lambda m: chr(int(m[1][1:], 16)) if len(m[1]) == 3 else escapes.get(m[1], m[1]), literal[1:-1])

    def _decide(self, sentence, show):
        """What the Lean function `show` makes of the tableau for `sentence`, which Lean builds
        for it."""
        return self._printed(f"Tableau.decide {json.dumps(sentence, ensure_ascii=False)} (String.quote ∘ {show})").strip()

    def _latex(self, letters):
        """The sentence letters `letters`, with their Greek letters and other such characters
        as LaTeX commands, as `pylatexenc` gives those: what goes in the fields of the format
        strings that Lean gives LaTeX as. Only the letters are turned into LaTeX here.
        `pylatexenc` gives `φ` as `\\ensuremath{\\varphi}`, and the `\\ensuremath` is taken
        off, since the LaTeX is in math mode already, and MathJax doesn't have it: a space is
        put after the command, if a letter comes after it, so that `φx` is `\\varphi x`."""
        return [_math(unicode_to_latex(a, non_ascii_only=True)) for a in letters]

    def _letters(self, sentence):
        """The sentence letters of `sentence`, as Lean gives them, in LaTeX."""
        return self._latex(self._eval(f"Tableau.letters {json.dumps(sentence, ensure_ascii=False)}").split(" "))

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
        tree of the LaTeX package `forest`, as `model_tex` gives it: a list, the branches from
        left to right, with one model for branches that describe the same, and empty if the
        tableau closes. They are the models of `models_lean`, in that order."""
        printed = self._tex(sentence, '(fun t s => "\\n".intercalate (t.modelsTex s))')
        return [model.strip() for model in printed.split("\n\n") if model.strip()]

    def models_lean(self, sentence):
        """The models that the open branches of the tableau for `sentence` describe, each as a
        Lean term, a model as `satisfied` and `model_tex` take one: a list, the branches from
        left to right, with one model for branches that describe the same, and empty if the
        tableau closes. Each is a countermodel: `sentence` is not `satisfied` by it."""
        printed = self._decide(sentence, '(fun t => "\\n\\n".intercalate t.modelsLean)')
        return printed.split("\n\n") if printed else []

    def satisfied(self, sentence, model):
        """Whether `sentence` holds in `model`, at its first world. A model is a Lean term of
        the decider's type `Tableau.Model`, a world and the worlds below it:

            { sees := [{ letters := ["p"], order := [["□q"], ["□p", "□r"]] }, {}] }

        `letters` are the sentence letters that hold at the world, `sees` the worlds just below
        it, each such a term, and `order` is for the boxed formulas that first hold at the
        world: those of a list are witnessed together, before those of the next list, and
        those in no list after them all, together. A field left out is empty, and `{}` is a
        world where no letter holds, with none below. The tree is read as the transitive order
        it generates: a boxed formula holds at a world if its formula holds at every world
        below, and `□A ≺ □B` if `□A` holds there and `□B` doesn't, or was witnessed after it,
        on the way down or in the order of the world where both first held.

        Every such term is a model of R⁻, so a sentence that is not satisfied by one is not a
        theorem of R⁻, and no tableau is built to see it. Raises `ValueError` if the sentence
        doesn't parse, if Lean doesn't read the model, or if it has a letter that isn't one or
        something in an order that isn't a boxed formula."""
        return self._eval(f"Tableau.satisfied {json.dumps(sentence, ensure_ascii=False)} ({model})") == "true"

    def model_tex(self, model):
        """The model `model`, a Lean term as `satisfied` takes one, as a tree of the LaTeX
        package `forest`, which also needs the package `amssymb` and the TikZ library
        `shapes.multipart`. The worlds are drawn as a tree, `w₀` the first and the others
        numbered on from it, each before the worlds below it, with an arrow from each to the
        worlds just below it; the arrows stand for the transitive order that generates. By
        each world is what holds there: its sentence letters, and the order of the boxed
        formulas that first hold there, `≺` between those witnessed one before the other and
        `≈` between those witnessed together. The boxed formulas are named `b₁`, `b₂` and so
        on there, and spelled out below the worlds. Only what first holds at a world is in its
        order, whatever the model has written there, since nothing else is ordered there.
        Raises `ValueError` as `satisfied` does."""
        letters, _, tex = self._printed(f"Tableau.model ({model}) (String.quote ∘ Tableau.Model.format)").partition("\n")
        return tex.format(*self._latex(letters.split(" "))).strip()

    def lean(self, sentence):
        """The tableau for `sentence` as a Lean file, which defines it as `t` and says, above
        it, what it shows: a record of the tableau, for a reader or for Lean. Lean is much
        slower to read it than to build the tableau, so nothing here does."""
        return self._decide(sentence, "Tableau.lean")
