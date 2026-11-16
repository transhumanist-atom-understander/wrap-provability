"""Two checks of the witness decider that need nothing from it but its sentence, in place of
the verifier that only GL's tableaux have.

`theorem` decides a sentence from Guaspari and Solovay's models of R⁻, by brute force: what a
tableau that closes must agree with.

`reduction` is the sentence of GL that says a sentence follows from the axioms that the
decider's rules replace, with each comparison a sentence letter: Guaspari and Solovay's
reduction of R⁻ to GL (Rosser sentences, 1979, 3.1), with those order axioms only. It is how a
tableau is drawn by hand, with the axioms as premises, and GL's decider decides it: what any
tableau of the witness decider must agree with.
"""

import functools
import itertools
import json
import re


def sentence(tableau):
    """The sentence of the Lean file `tableau`, as nested tuples of a constructor's name and
    its arguments: `("imp", ("box", ("atom", "p")), ("bot",))` for `□p → ⊥`."""
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"|[()]|\.\w+', re.search(r"^  sentence := (.*)$", tableau, re.M)[1])

    def term():
        match tokens.pop(0):
            case "(":
                name, arguments = tokens.pop(0)[1:], []
                while tokens[0] != ")":
                    arguments.append(term())
                tokens.pop(0)
                return (name, *arguments)
            case ".bot":
                return ("bot",)
            case letter:
                return ("atom", json.loads(letter))

    return term()


def subformulas(A):
    """`A`'s subformulas, with the boxed formulas its comparisons compare, and `□¬B` for `◇B`."""
    match A:
        case ("prec" | "preceq", B, C):
            return {A} | subformulas(("box", B)) | subformulas(("box", C))
        case ("dia", B):
            return {A} | subformulas(("box", ("neg", B)))
        case _:
            return {A}.union(*(subformulas(B) for B in A[1:] if isinstance(B, tuple)))


# The models of R⁻
#
# A sentence `A` is a theorem of R⁻ iff it holds at the root of every `A`-model: a finite tree,
# each node of which decides the sentence letters, which boxed subformulas of `A` hold there
# (those whose formula holds at every node below), and the order in which they were witnessed, a
# total preorder. Witnessing persists: what holds at a node holds below it, in the same order,
# before what comes to hold there. So `□B ≼ □C` holds where `□B` holds and `□C` doesn't, or isn't
# witnessed before `□B`, and `□B ≺ □C` where `□B` holds and `□C` doesn't, or is witnessed after.


def preorders(boxed):
    """The total preorders of `boxed`, each a list of the sets witnessed together, first to
    last."""
    if not boxed:
        yield []
    for size in range(1, len(boxed) + 1):
        for first in itertools.combinations(boxed, size):
            for rest in preorders([B for B in boxed if B not in first]):
                yield [first, *rest]


def theorem(A):
    """Whether `A`, as `sentence` gives it, is a theorem of R⁻. The search decides every boxed
    subformula and every order at every node: it is exponential in the number of boxed
    subformulas, so it is for small sentences."""
    boxed = sorted((B[1] for B in subformulas(A) if B[0] == "box"), key=repr)
    letters = sorted(B[1] for B in subformulas(A) if B[0] == "atom")

    def holds(B, when, letter):
        """Whether `B` holds at a node: `when[C]` is when `□C`, which holds there, was
        witnessed, and `letter[p]` is whether the sentence letter `p` holds there."""
        match B:
            case ("atom", p):
                return letter[p]
            case ("bot",):
                return False
            case ("neg", C):
                return not holds(C, when, letter)
            case ("and", C, D):
                return holds(C, when, letter) and holds(D, when, letter)
            case ("or", C, D):
                return holds(C, when, letter) or holds(D, when, letter)
            case ("imp", C, D):
                return not holds(C, when, letter) or holds(D, when, letter)
            case ("iff", C, D):
                return holds(C, when, letter) == holds(D, when, letter)
            case ("box", C):
                return C in when
            case ("dia", C):
                return ("neg", C) not in when
            case ("prec", C, D):
                return C in when and (D not in when or when[C] < when[D])
            case ("preceq", C, D):
                return C in when and (D not in when or when[C] <= when[D])

    @functools.cache
    def node(required, above):
        """Whether some model has a node where the formulas `required` hold, below a node
        where the boxed formulas were witnessed as in `above`, the items of a `when`. It may be
        taken to have, for each `□B` that doesn't hold at it, a node just below where `B`
        doesn't hold and `□B` does, and no other node just below."""
        above = dict(above)
        now = max(above.values(), default=0)
        rest = [B for B in boxed if B not in above]
        for size in range(len(rest) + 1):
            for new in itertools.combinations(rest, size):
                for order in preorders(new):
                    when = above | {B: now + 1 + n for n, together in enumerate(order) for B in together}
                    for values in itertools.product([False, True], repeat=len(letters)):
                        letter = dict(zip(letters, values))
                        if all(holds(B, when, letter) for B in (*required, *above)) and all(
                            node((("neg", B), ("box", B)), tuple(sorted(when.items(), key=repr)))
                            for B in boxed
                            if B not in when
                        ):
                            return True
        return False

    return not node((("neg", A),), ())


# The reduction to GL


def axioms(c):
    """The axioms of R⁻ that the decider's rules for the comparison `c` replace. For `c` the
    comparison `□B ≺ □C` or `□B ≼ □C`: it persists, true comes before false, its first formula
    is true, and false never comes before true."""
    B, C = ("box", c[1]), ("box", c[2])
    return [
        ("imp", c, ("box", c)),
        ("imp", ("and", B, ("neg", C)), c),
        ("imp", c, B),
        ("imp", ("and", C, ("neg", B)), ("box", ("neg", c))),
    ]


def reduction(A):
    """The sentence of GL, as the deciders read one, that says `A` follows from `axioms`, at
    the world where it is evaluated and at the worlds that one sees, for each comparison in
    `A`. A comparison is the sentence letter `≺0`, `≺1`, ..., which no sentence letter of `A`
    can be."""
    comparisons = sorted((B for B in subformulas(A) if B[0] in ("prec", "preceq")), key=repr)
    letter = {c: ("atom", f"≺{n}") for n, c in enumerate(comparisons)}

    def spell(B):
        if B in letter:
            return letter[B][1]
        match B:
            case ("atom", p):
                return p
            case ("bot",):
                return "⊥"
            case ("neg", C):
                return "¬" + spell(C)
            case ("box", C):
                return "□" + spell(C)
            case ("dia", C):
                return "◇" + spell(C)
            case (connective, C, D):
                symbol = {"and": "∧", "or": "∨", "imp": "→", "iff": "↔"}[connective]
                return f"({spell(C)} {symbol} {spell(D)})"

    premises = [f"⊡{spell(X)}" for c in comparisons for X in axioms(c)]
    return " → ".join([*premises, spell(A)])
