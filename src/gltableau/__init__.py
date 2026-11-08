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
`Decider` runs the decider's server `tableau`, and a `Verifier` the verifier's `verify`, with
`lake build` and then `lake exe` in that directory, and keeps it running: it starts by loading
its Lean library, which for the verifier takes a couple of seconds, after which every request
is fast.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

PROOF = "\ntheorem proof : t.verdict := t.verified\n"


class LeanError(Exception):
    """Lean rejected the source: the message is its errors."""


class Server:
    """A server of one of the Lean projects: `lake exe EXE` run in the project's directory,
    after `lake build` there, so that the library it loads is built, and spoken to until the
    `with` block ends."""

    exe: str

    def __init__(self, project):
        self.project = Path(project)
        if not (self.project / "lakefile.toml").is_file():
            raise FileNotFoundError(f"no Lean project at {self.project}")
        try:
            build = subprocess.run(["lake", "build"], cwd=self.project, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            raise FileNotFoundError("lake is not on the path: install Lean with elan") from None
        if build.returncode:
            raise LeanError(f"`lake build` in {self.project} failed:\n{build.stdout}")
        self.lean = subprocess.Popen(["lake", "exe", self.exe], cwd=self.project, text=True,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.lean.stdin.close()
        self.lean.wait()

    def _ask(self, **request):
        self.lean.stdin.write(json.dumps(request) + "\n")
        self.lean.stdin.flush()
        reply = self.lean.stdout.readline()
        if not reply:
            raise LeanError(f"`lake exe {self.exe}` in {self.project} exited without answering")
        return json.loads(reply)

    def _run(self, source):
        """What the `#eval`s of the Lean file `source` print, its `import`s taken to be the
        server's library."""
        reply = self._ask(lean=source)
        if reply["errors"]:
            raise LeanError(reply["errors"])
        return reply["output"]


class Decider(Server):
    """The server `tableau` of `decide-provability`, at `project`."""

    exe = "tableau"

    def tableau(self, sentence):
        """The tableau for `sentence`, with letters as sentence letters, `¬ □ ◇ ⊡` binding
        tightest, then `∧`, `∨`, `→`, `↔`, each associating to the right: a Lean file defining
        it as `t`."""
        reply = self._ask(sentence=sentence)
        if "error" in reply:
            raise ValueError(reply["error"])
        return reply["lean"]

    def closed(self, tableau):
        """Whether the tableau of the Lean file `tableau` closed, so its sentence is a theorem
        of GL."""
        return self._run(tableau + "\n#eval IO.print t.tree.isClosed") == "true"

    def tex(self, tableau):
        """The tableau of the Lean file `tableau` as a `prooftree` of the LaTeX package
        `prooftrees`."""
        return self._run(tableau + "\n#eval IO.print t.tex")

    def sentence_tex(self, tableau):
        """The sentence of the Lean file `tableau` in LaTeX, for math mode."""
        return self._run(tableau + "\n#eval IO.print (t.sentence.render .tex)")


class Verifier(Server):
    """The server `verify` of `verify-provability`, at `project`."""

    exe = "verify"

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
