from types import ModuleType

from streamlink import Streamlink
from streamlink.plugin import Plugin
from streamlink.utils import load_module


class Client(Streamlink):

    def __init__(self, *args, **kwargs):
        rubrick = kwargs.pop("name_rubrick", r"{project}.plugins.{name}")
        super().__init__(*args, **kwargs)
        self._name_rubrick = rubrick

    def add_plugin(self, plugin: Plugin, name: str = "unknown") -> Plugin:
        plugin.bind(self, name, self.get_option("user-input-requester"))
        self.plugins[plugin.module] = plugin
        return self.plugins[plugin.module]

