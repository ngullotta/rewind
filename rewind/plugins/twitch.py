import logging
import os
from typing import Any, Dict, List, OrderedDict, Union

from streamlink.plugin import PluginArgument, PluginArguments
from streamlink.plugin.api import validate
from streamlink.plugins.twitch import Twitch, TwitchAPI
from streamlink_cli.main import args
from tabulate import tabulate

StreamReturnType = Union[OrderedDict, None]
NodeList = List[Dict]


class NodePrompt:
    limit = int(os.popen("stty size", "r").read().split()[-1]) // 2

    def __init__(self, nodes: NodeList, filter: set = {}) -> None:
        if len(nodes) > 0:
            filter = filter if len(filter) > 0 else nodes[-1].keys()

        if "title" in filter:
            for node in nodes:
                node["title"] = self.truncate(node.get("title", ""))

        self.nodes = [
            {k: node.get(k) for k in node.keys() & filter} for node in nodes
        ]

    def truncate(self, key: str, filler: str = "...") -> str:
        if len(key) > self.limit:
            return key[0 : self.limit - len(filler)] + filler
        return key

    @staticmethod
    def clamp(value: int, lower: int, upper: int) -> int:
        return max(lower, min(value, upper))

    @staticmethod
    def user_input_prompter(text: str = "Pick a Past Broadcast: ") -> Any:
        while (raw := input(text)) != "":
            if raw.isnumeric():
                return int(raw)
            print("That doesn't look like an integer...")
        return 0

    def __call__(self) -> int:
        print(tabulate(self.nodes, headers="keys", showindex=True))
        idx = self.user_input_prompter()
        idx = self.clamp(idx, 0, len(self.nodes))
        return self.nodes[idx].get("id")


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

            prompter = NodePrompt(
                nodes, filter={"id", "title", "lengthSeconds", "publishedAt"}
            )
            self.video_id = prompter()

        return self._get_streams()


__plugin__ = TwitchRewind
