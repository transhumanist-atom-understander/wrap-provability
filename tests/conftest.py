"""The decider, found at `$GL_DECIDER` as the command finds it and started once for the whole
run; the tests are skipped if it isn't set."""

import functools
import os

import pytest

from gltableau import Decider


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
