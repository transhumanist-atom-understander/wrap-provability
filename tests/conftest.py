"""The decider and the verifier, found at `$GL_DECIDER` and `$GL_VERIFIER` as the commands find
them, each started once for the whole run; tests needing one that isn't set are skipped."""

import functools
import os

import pytest

from gltableau import Decider, Verifier


def project(variable):
    if variable not in os.environ:
        pytest.skip(f"${variable} is not set to a checkout of the Lean project")
    return os.environ[variable]


@pytest.fixture(scope="session")
def decider():
    with Decider(project("GL_DECIDER")) as d:
        yield d


@pytest.fixture(scope="session")
def verifier():
    with Verifier(project("GL_VERIFIER")) as v:
        yield v


@pytest.fixture(scope="session")
def tableau(decider):
    """The decider's tableau for a sentence, as a Lean file, computed once per sentence."""
    return functools.cache(decider.tableau)
