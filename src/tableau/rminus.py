"""Tableaux for sentences of R⁻, the logic of Guaspari and Solovay: GL with the witness
comparisons `□A ≺ □B` and `□A ≼ □B` of Rosser sentences.

    with Decider(decider) as d:
        t = d.tableau("□(□⊤ ≺ □⊥)")       # the tableau as a Lean file
        d.closed(t)                       # whether it closed, so the sentence is a theorem of R⁻
        d.tex(t)                          # the tableau as a LaTeX prooftree
        d.sentence_tex(t)                 # the sentence in LaTeX

There is no verifier of these tableaux yet.
"""

import sys
from pathlib import Path

import tableau
from tableau import LeanError, project


class Decider(tableau.Decider):
    """The REPL of `decide-provability`, at `project`, with `RMinusTableau` imported: the
    tableau for a sentence, which is written as a sentence of GL is, with `□A ≺ □B` and
    `□A ≼ □B`, which bind tighter than `∧` and looser than `¬ □ ◇ ⊡`: what they compare must be
    written as boxed formulas."""

    module = "RMinusTableau"
    namespace = "RMinus.Tableau"


def main():
    """rminus-tableau tableau SENTENCE  prints the tableau as a Lean file; exits 1 if it is open
    rminus-tableau tex FILE          prints the tableau in the Lean file as a LaTeX prooftree

    $GL_DECIDER is the directory of decide-provability."""
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
            case _:
                sys.exit(main.__doc__)
    except (ValueError, LeanError, FileNotFoundError) as e:
        sys.exit(str(e))
