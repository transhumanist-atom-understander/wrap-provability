"""The decider, found at `$DECIDE_PROVABILITY` and started once for the whole run; the tests are
skipped if it isn't set."""

import os

import pytest

from rtableau import Decider


@pytest.fixture(scope="session")
def decider():
    if "DECIDE_PROVABILITY" not in os.environ:
        pytest.skip("$DECIDE_PROVABILITY is not set to a checkout of the Lean project")
    with Decider(os.environ["DECIDE_PROVABILITY"]) as d:
        yield d
