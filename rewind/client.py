from streamlink import Streamlink
from streamlink.plugin import Plugin

from rewind.plugins import TwitchRewind


class Client(Streamlink):

    REWIND_OVERWRITES = {
        "twitch": TwitchRewind
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, plugin in self.REWIND_OVERWRITES.items():
            self.add_plugin(plugin, name)

    def add_plugin(self, plugin: Plugin, name: str = "unknown") -> Plugin:
        plugin.bind(self, name, self.get_option("user-input-requester"))
        self.plugins[plugin.module] = plugin
        return self.plugins[plugin.module]
