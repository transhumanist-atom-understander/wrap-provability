"""GL tableaux, checked by Lean.

    with Decider() as d:
        t = d.tableau("□(□p → p) → □p")   # t.theorem, and t.lean, the tableau as a Lean file
        d.tex(t.lean)                     # the tableau as a LaTeX prooftree
        d.verify(t.lean)                  # a Lean proof that the tableau's verdict is right

A `Decider` runs the `tableau` server of the Lean project `gl-tableau`, found at `$GL_TABLEAU`
or beside this checkout, and keeps it running: it starts by loading the Lean library, which
takes a couple of seconds, after which every request is fast.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT = Path(os.environ.get("GL_TABLEAU", Path(__file__).parents[3] / "gl-tableau"))

PROOF = "\ntheorem proof : t.verdict := t.verified\n"


class LeanError(Exception):
    """Lean rejected the source: the message is its errors."""


@dataclass
class Tableau:
    theorem: bool
    """Whether the tableau closed, so the sentence is a theorem of GL."""
    lean: str
    """The tableau as a Lean file, defining it as `t`."""


class Decider:
    def __init__(self, project=PROJECT):
        if not Path(project, "lakefile.toml").is_file():
            raise FileNotFoundError(f"no Lean project at {project}: set GL_TABLEAU to gl-tableau's directory")
        self.lean = subprocess.Popen(["lake", "exe", "tableau"], cwd=project, text=True,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.lean.stdin.close()
        self.lean.wait()

    def _ask(self, **request):
        self.lean.stdin.write(json.dumps(request) + "\n")
        self.lean.stdin.flush()
        return json.loads(self.lean.stdout.readline())

    def _run(self, source):
        """What the `#eval`s of the Lean file `source` print, its header taken to be
        `import GLTableau`."""
        reply = self._ask(lean=source)
        if reply["errors"]:
            raise LeanError(reply["errors"])
        return reply["output"]

    def tableau(self, sentence):
        """The tableau for `sentence`, with letters as sentence letters, `¬ □ ◇ ⊡` binding
        tightest, then `∧`, `∨`, `→`, `↔`, each associating to the right."""
        reply = self._ask(sentence=sentence)
        if "error" in reply:
            raise ValueError(reply["error"])
        return Tableau(reply["closed"], reply["lean"])

    def tex(self, tableau):
        """The tableau of the Lean file `tableau` as a `prooftree` of the LaTeX package
        `prooftrees`."""
        return self._run(tableau + "\n#eval IO.print t.tex")

    def verify(self, tableau):
        """The Lean file `tableau` with a proof of its verdict, that its sentence is or is not
        in `LogicGL` of `ProvabilityLogic`, checked by Lean; raises `LeanError` if it fails."""
        self._run(tableau + PROOF)
        return tableau + PROOF


def main():
    """gl-tableau tableau SENTENCE  prints the tableau as a Lean file; exits 1 if it is open
    gl-tableau tex FILE           prints the tableau in the Lean file as a LaTeX prooftree
    gl-tableau verify FILE        prints the Lean file with a proof of its verdict, checked"""
    try:
        with Decider() as d:
            match sys.argv[1:]:
                case ["tableau", sentence]:
                    t = d.tableau(sentence)
                    print(t.lean, end="")
                    sys.exit(not t.theorem)
                case ["tex", file]:
                    print(d.tex(Path(file).read_text()), end="")
                case ["verify", file]:
                    print(d.verify(Path(file).read_text()), end="")
                case _:
                    sys.exit(main.__doc__)
    except (ValueError, LeanError, FileNotFoundError) as e:
        sys.exit(str(e))
