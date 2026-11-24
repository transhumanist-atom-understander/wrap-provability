"""A check of the decider's tableaux for sentences with witness comparisons, that needs nothing
from it but its sentence: `theorem` decides a sentence from Guaspari and Solovay's models of
R⁻, by brute force, and a tableau closes exactly when it says so.

And a check of what the decider says holds in a model, that needs nothing from it at all:
`satisfied` works that out again, from what it is for a formula to hold at a world.
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


# One model
#
# A model as the decider has one, a Lean term: here a dict of a world's `letters`, its `order`,
# lists of formulas `B` for the boxed formulas `□B` witnessed together, and the worlds it `sees`
# just below it, each such a dict.


def spelled(A):
    """`A` written as a sentence, with parentheses around every formula of two."""
    match A:
        case ("atom", p):
            return p
        case ("bot",):
            return "⊥"
        case ("neg" | "box" | "dia", B):
            return {"neg": "¬", "box": "□", "dia": "◇"}[A[0]] + spelled(B)
        case ("prec" | "preceq", B, C):
            return f"(□{spelled(B)} {'≺' if A[0] == 'prec' else '≼'} □{spelled(C)})"
        case (connective, B, C):
            return f"({spelled(B)} {dict(zip(['and', 'or', 'imp', 'iff'], '∧∨→↔'))[connective]} {spelled(C)})"


def term(model):
    """The Lean term for `model`."""
    strings = lambda items: "[" + ", ".join(json.dumps(item, ensure_ascii=False) for item in items) + "]"
    order = "[" + ", ".join(strings("□" + spelled(B) for B in together) for together in model["order"]) + "]"
    sees = "[" + ", ".join(term(world) for world in model["sees"]) + "]"
    return f"{{ letters := {strings(model['letters'])}, order := {order}, sees := {sees} }}"


def satisfied(A, model):
    """Whether `A` holds at the first world of `model`, straight from what that means: a formula
    is asked of the worlds on the way down to one, the first world first."""

    def below(world):
        """The ways down from `world`, to each world below it."""
        for next in world["sees"]:
            yield [next]
            yield from ([next, *rest] for rest in below(next))

    def witnessed(B, way):
        """When `□B` was witnessed on the `way` down: how far down, and where in the order of
        the world there. `None` if it doesn't hold at the end of the way."""
        for far in range(len(way)):
            if true(("box", B), way[: far + 1]):
                order = way[far]["order"]
                return far, next((n for n, together in enumerate(order) if B in together), len(order))

    def true(B, way):
        match B:
            case ("box", C):
                return all(true(C, way + rest) for rest in below(way[-1]))
            case ("dia", C):
                return any(true(C, way + rest) for rest in below(way[-1]))
            case ("prec" | "preceq", C, D):
                c, d = witnessed(C, way), witnessed(D, way)
                return c is not None and (d is None or (c < d if B[0] == "prec" else c <= d))
            case ("neg", C):
                return not true(C, way)
            case ("atom", p):
                return p in way[-1]["letters"]
            case ("bot",):
                return False
            case (connective, C, D):
                c, d = true(C, way), true(D, way)
                return {"and": c and d, "or": c or d, "imp": not c or d, "iff": c == d}[connective]

    return true(A, [model])
