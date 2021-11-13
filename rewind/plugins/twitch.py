import logging
from datetime import timedelta
from typing import OrderedDict, Union

from streamlink.plugin import PluginArgument, PluginArguments
from streamlink.plugin.api import validate
from streamlink.plugins.twitch import Twitch, TwitchAPI

StreamReturnType = Union[OrderedDict, None]


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

        nodes = self.api.video_tower(self.channel)
        for node in nodes:
            _id = node.get("id", "")
            title = node.get("title", "")
            print(
                _id,
                "->",
                title,
                timedelta(seconds=node.get("lengthSeconds")),
                node.get("game", {}).get("name"),
            )
            if _id:
                self.video_id = _id
                break

        return self._get_streams()


__plugin__ = TwitchRewind
