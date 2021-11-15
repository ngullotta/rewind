import logging
from datetime import timedelta
from typing import Any, List, OrderedDict, Union

from streamlink.plugin import PluginArgument, PluginArguments
from streamlink.plugin.api import validate
from streamlink.plugins.twitch import Twitch, TwitchAPI
from tabulate import tabulate

StreamReturnType = Union[OrderedDict, None]
NodeList = List[dict]


class Node(dict):
    __default_whitelist = ["id", "title"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.whitelist = kwargs.pop("whitelist", self.__default_whitelist)
        self._cull()

    def _cull(self):
        keys = [k for k in self.keys() if k not in self.whitelist]
        for k in keys:
            del self[k]

    def __setitem__(self, k, v) -> Any:
        if k in self.whitelist.keys():
            return super().__setitem__(k, v)


class NodePrompt:
    def __init__(self, nodes: NodeList) -> None:
        self.nodes = [Node(node) for node in nodes]

    @staticmethod
    def clamp(value: int, lower: int, upper: int) -> int:
        return max(upper, min(lower, value))

    @staticmethod
    def prompt_user_for_selection(
        text: str = "Pick a number:", _type: Any = int
    ) -> Any:
        while (raw := input(text)) != "":
            if raw.isnumeric():
                return _type(raw)
            print(f'That doesn\'t look like a "{_type.__name__}"...')
        return _type()

    def make_prompt(self, **tab_kwargs) -> str:
        return tabulate(self.nodes, **tab_kwargs)

    def run_prompt(self, attr: str = "id") -> int:
        print(self.make_prompt(headers="keys", showindex=True))
        idx = self.prompt_user_for_selection()
        idx = self.clamp(idx, len(self.nodes), 1)
        return self.nodes[idx - 1].get("id")


class TwitchAPIRewind(TwitchAPI):
    def video_tower(self, channel: str, limit: int = 30) -> dict:
        query = self._gql_persisted_query(
            "FilterableVideoTower_Videos",
            "a937f1d22e269e39a03b509f65a7490f9fc247d7f83d6ac1421523e3b68042cb",
            broadcastType="ARCHIVE",
            channelOwnerLogin=channel,
            limit=limit,
            videoSort="TIME",
        )

        schema = validate.Schema(
            {"data": {"user": {"videos": {"edges": list}}}},
            validate.get(("data", "user", "videos", "edges"), []),
            validate.map(lambda edge: edge["node"]),
        )

        return self.call(query, schema=schema)


class TwitchRewind(Twitch):

    logger = logging.getLogger("TwitchRewind")

    # pylint: disable=unnecessary-comprehension
    arguments = PluginArguments(
        *[argument for argument in Twitch.arguments.arguments.values()],
        PluginArgument(
            "check-vods",
            action="store_true",
            help="""
            Check for VODs (Videos On Demand) if the selected streamer is
            notcurrently streaming.
            """,
        ),
        PluginArgument(
            "pick-most-recent-vod",
            action="store_true",
            help="""
            Check for VODs (Videos On Demand) if the selected streamer is
            notcurrently streaming.
            """,
        ),
        PluginArgument(
            "vod-check-limit",
            default=10,
            help="""
            Limit VODs to X most recent
            """,
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.api = TwitchAPIRewind(self.api.session)

    def _get_streams(self) -> StreamReturnType:
        streams = super()._get_streams()
        if streams is not None:
            return streams

        self.logger.info(
            f"Channel {self.channel} is not currently streaming..."
        )

        if not self.options.get("check_vods"):
            return None

        return self._check_past_broadcasts()

    def _check_past_broadcasts(self) -> StreamReturnType:
        self.logger.info("Checking for past broadcasts...")

        if nodes := self.api.video_tower(self.channel):
            if self.options.get("pick_most_recent_vod"):
                for node in nodes:
                    self.video_id = node.get("id")
                    return

            prompter = NodePrompt(nodes)
            self.video_id = prompter.run_prompt()

        return self._get_streams()


__plugin__ = TwitchRewind
