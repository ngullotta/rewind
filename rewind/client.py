from streamlink import Streamlink
from streamlink.plugin import Plugin


class Client(Streamlink):

    def add_plugin(self, plugin: Plugin, name: str = "unknown") -> Plugin:
        plugin.bind(self, name, self.get_option("user-input-requester"))
        self.plugins[plugin.module] = plugin
        return self.plugins[plugin.module]
