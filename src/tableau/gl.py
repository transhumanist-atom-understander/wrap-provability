"""Tableaux for sentences of GL, Gödel–Löb provability logic, checked by Lean.

    with Decider(decider) as d:
        t = d.tableau("□(□p → p) → □p")   # the tableau as a Lean file
        d.closed(t)                       # whether it closed, so the sentence is a theorem of GL
        d.tex(t)                          # the tableau as a LaTeX prooftree
        d.sentence_tex(t)                 # the sentence in LaTeX
    with Verifier(verifier) as v:
        v.verify(t)                       # a Lean proof that the tableau's verdict is right
"""

import sys
from pathlib import Path

import tableau
from tableau import LeanError, Server, project

PROOF = "\ntheorem proof : t.verdict := t.verified\n"


class Decider(tableau.Decider):
    """The REPL of `decide-provability`, at `project`, with `GLTableau` imported: the tableau
    for a sentence, where a sentence letter is any run of characters other than whitespace,
    parentheses and the connectives, `¬ □ ◇ ⊡` bind tightest, then `∧`, `∨`, `→`, `↔`, each
    associating to the right."""

    module = "GLTableau"
    namespace = "Tableau"


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
