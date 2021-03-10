import pytest
from rewind import Client
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


def test_twitch_get_vods(plugin):
    streams = plugin.streams()
    assert(streams)
