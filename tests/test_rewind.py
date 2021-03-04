from os.path import exists
from pathlib import Path

import pytest
import rewind
from rewind import Client, __version__
from rewind.plugins import TwitchRewind


@pytest.fixture()
def session():
    yield Client()

@pytest.fixture()
def plugin(session):
    session.add_plugin(TwitchRewind, name="twitch")
    yield TwitchRewind("https://www.twitch.tv/clintstevens")

def test_twitch(session, plugin):
    assert(plugin)
    assert(session)
    pass
