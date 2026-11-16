"""The deciders, found at `$GL_DECIDER` as the commands find them, each started once for the
whole run; the tests are skipped if it isn't set."""

import functools
import os

import pytest

from rtableau import Decider, WitnessDecider


def project(variable):
    if variable not in os.environ:
        pytest.skip(f"${variable} is not set to a checkout of the Lean project")
    return os.environ[variable]


@pytest.fixture(scope="session")
def decider():
    with Decider(project("GL_DECIDER")) as d:
        yield d


@pytest.fixture(scope="session")
def tableau(decider):
    """The decider's tableau for a sentence, as a Lean file, computed once per sentence."""
    return functools.cache(decider.tableau)


@pytest.fixture(scope="session")
def witness_decider():
    with WitnessDecider(project("GL_DECIDER")) as d:
        yield d


@pytest.fixture(scope="session")
def witness_tableau(witness_decider):
    """The witness decider's tableau for a sentence, as a Lean file, computed once per sentence."""
    return functools.cache(witness_decider.tableau)
