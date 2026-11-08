"""GL tableaux, checked by Lean.

    with Decider(decider) as d:
        t = d.tableau("□(□p → p) → □p")   # the tableau as a Lean file
        d.closed(t)                       # whether it closed, so the sentence is a theorem of GL
        d.tex(t)                          # the tableau as a LaTeX prooftree
        d.sentence_tex(t)                 # the sentence in LaTeX
    with Verifier(verifier) as v:
        v.verify(t)                       # a Lean proof that the tableau's verdict is right

`decider` and `verifier` are the directories of checkouts of the Lean projects
`decide-provability` and `verify-provability`; there is no default, each must be given. A
`Decider` or `Verifier` builds its project, with `lake build`, and runs the Lean REPL that the
project requires in it, through `lean-interact`, with the project's library imported, which
for the verifier takes a couple of seconds; after that every request is fast.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from lean_interact import Command, LeanREPLConfig, LeanServer, LocalProject
from lean_interact.interface import LeanError as REPLError
from pylatexenc.latexencode import unicode_to_latex

PROOF = "\ntheorem proof : t.verdict := t.verified\n"


class LeanError(Exception):
    """Lean rejected the source: the message is its errors."""


class Server(LeanServer):
    """The Lean REPL run in one of the Lean projects, after `lake build` there, and spoken to
    until the `with` block ends. Each request is a Lean file importing the project's library,
    `module`, which the REPL loads once, at the start, and reuses."""

    module: str

    def __init__(self, project):
        lean = LocalProject(directory=project, auto_build=False)
        try:
            lean.build(verbose=False)
        except subprocess.CalledProcessError:
            raise LeanError(f"`lake build` in {project} failed: run it there to see why") from None
        super().__init__(LeanREPLConfig(project=lean, local_repl_path=Path(project, ".lake/packages/REPL")))
        self._run(f"import {self.module}")

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


class Decider(Server):
    """The REPL of `decide-provability`, at `project`, with `GLTableau` imported."""

    module = "GLTableau"

    def tableau(self, sentence):
        """The tableau for `sentence`, where a sentence letter is any run of characters other
        than whitespace, parentheses and the connectives, `¬ □ ◇ ⊡` bind tightest, then `∧`,
        `∨`, `→`, `↔`, each associating to the right: a Lean file defining it as `t`."""
        try:
            return self._run(f"import {self.module}\n#eval Tableau.decide {json.dumps(sentence, ensure_ascii=False)}")
        except LeanError as e:
            raise ValueError(str(e)) from None

    def closed(self, tableau):
        """Whether the tableau of the Lean file `tableau` closed, so its sentence is a theorem
        of GL."""
        return self._run(tableau + "\n#eval IO.print t.tree.isClosed") == "true"

    def tex(self, tableau):
        """The tableau of the Lean file `tableau` as a `prooftree` of the LaTeX package
        `prooftrees`."""
        return self._tex(tableau + "\n#eval IO.print t.tex")

    def sentence_tex(self, tableau):
        """The sentence of the Lean file `tableau` in LaTeX, for math mode."""
        return self._tex(tableau + "\n#eval IO.print (t.sentence.render .tex)")


class Verifier(Server):
    """The REPL of `verify-provability`, at `project`, with `GLVerify` imported."""

    module = "GLVerify"

    def verify(self, tableau):
        """The Lean file `tableau` with a proof of its verdict, that its sentence is or is not
        in `LogicGL` of `ProvabilityLogic`, checked by Lean; raises `LeanError` if it fails.
        The file imports `GLVerify`, the verifier's library, so that it checks on its own in
        that project too."""
        source = tableau.replace("import GLTableau\n", "import GLVerify\n", 1) + PROOF
        self._run(source)
        return source


def project(variable):
    """The directory the environment variable names, or exit explaining it must."""
    try:
        return os.environ[variable]
    except KeyError:
        sys.exit(f"set {variable} to the directory of a checkout of the Lean project")


def main():
    """gl-tableau tableau SENTENCE  prints the tableau as a Lean file; exits 1 if it is open
    gl-tableau tex FILE           prints the tableau in the Lean file as a LaTeX prooftree
    gl-tableau verify FILE        prints the Lean file with a proof of its verdict, checked

    $GL_DECIDER is the directory of decide-provability, $GL_VERIFIER that of verify-provability."""
    try:
        match sys.argv[1:]:
            case ["tableau", sentence]:
                with Decider(project("GL_DECIDER")) as d:
                    t = d.tableau(sentence)
                    print(t, end="")
                    sys.exit(not d.closed(t))
            case ["tex", file]:
                with Decider(project("GL_DECIDER")) as d:
                    print(d.tex(Path(file).read_text()), end="")
            case ["verify", file]:
                with Verifier(project("GL_VERIFIER")) as v:
                    print(v.verify(Path(file).read_text()), end="")
            case _:
                sys.exit(main.__doc__)
    except (ValueError, LeanError, FileNotFoundError) as e:
        sys.exit(str(e))
