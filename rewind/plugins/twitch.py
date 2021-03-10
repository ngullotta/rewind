import logging
from datetime import datetime, timedelta, timezone
from typing import List, OrderedDict, Union

from requests import HTTPError
from streamlink.plugin import PluginArgument, PluginArguments, PluginError
from streamlink.plugins.twitch import Twitch


class TwitchVOD:

    def __init__(self, data: dict) -> None:
        self.data = data
        self._streams = OrderedDict()

    @staticmethod
    def _parse_date_str(date: str) -> datetime:
        if date is not None and date.endswith("Z"):
            date = date[:-1] + "+00:00"

        try:
            date = datetime.fromisoformat(date)
            date = date.replace(tzinfo=timezone.utc).astimezone(tz=None)
            return date
        except (TypeError, ValueError):
            pass

        return datetime.utcfromtimestamp(0)

    @property
    def id(self) -> str:
        return self.data.get("_id", "")[1:]

    @property
    def title(self) -> str:
        return self.data.get("title", "")

    @property
    def url(self) -> str:
        return self.data.get("url", "")

    @property
    def viewable(self) -> bool:
        return self.data.get("viewable", "private") == "public"

    @property
    def date(self) -> datetime:
        created = self.data.get("created_at")
        return self._parse_date_str(created)

    @property
    def length(self) -> timedelta:
        seconds = self.data.get("length", 0)
        return timedelta(seconds=seconds)

    @property
    def game(self) -> str:
        return self.data.get("game", "Unkown")

    @property
    def streams(self) -> OrderedDict:
        return self._streams

    @streams.setter
    def streams(self, value: OrderedDict) -> OrderedDict:
        self._streams = value
        return self.streams


class TwitchRewind(Twitch):

    logger = logging.getLogger("TwitchRewind")

    arguments = PluginArguments(
        *[
            argument for argument in Twitch.arguments.arguments.values()
        ],

        PluginArgument(
            "check-vods",
            action="store_true",
            help="""
            Check for VODs (Videos On Demand) if the selected streamer is
            notcurrently streaming.
            """
        ),

        PluginArgument(
            "pick-most-recent-vod",
            action="store_true",
            help="""
            Check for VODs (Videos On Demand) if the selected streamer is
            notcurrently streaming.
            """
        ),

        PluginArgument(
            "vod-check-limit",
            default=10,
            help="""
            Limit VODs to X most recent
            """
        )
    )

    def _parse_video_data(self, response: dict) -> List[TwitchVOD]:
        vod_list = []
        for data in response.get("videos", []):
            vod_list.append(TwitchVOD(data))
        return vod_list

    def _fill_vod_stream(self, vod: TwitchVOD) -> None:
        tmp = self.video_id

        try:
            self.video_id = vod.id
            vod.streams = self._get_hls_streams_video()
        except (Exception):
            pass
        finally:
            self.video_id = tmp

    def _get_vods(self) -> OrderedDict:
        vods = OrderedDict()
        try:
            res = self._get_videos(broadcast_type="archive")
            for vod in self._parse_video_data(res):
                self._fill_vod_stream(vod)
                vods[vod.id] = vod
            return OrderedDict(
                sorted(vods.items(), key=lambda obj: obj[1].date, reverse=True)
            )
        except (PluginError, HTTPError) as e:
            self.logger.error(e)
        finally:
            return vods

    def _get_videos(self, **kwargs) -> dict:
        return self.api.call(
            f"/kraken/channels/{self.channel_id}/videos",
            **kwargs
        )

    def _check_vods(self) -> Union[OrderedDict, None]:
        if not self.options.get("check_vods"):
            return

        vods = self._get_vods()
        if len(vods) == 0:
            return

        vlist = list(vods.values())
        if self.options.get("pick_most_recent_vod"):
            return self.vods[0]

        for i, vod in enumerate(vlist):
            print(
                f"[{i + 1:2d}] {vod.date} | ({vod.id}) {vod.title} {vod.game}"
            )

        try:
            choice = int(input("Pick a VOD: "))
            if choice < 0:
                choice = 0
            if choice > len(vlist):
                choice = len(vlist)
        except (ValueError):
            choice = 1
        except (KeyboardInterrupt):
            choice = 1
        return vlist[choice - 1].streams

    def _get_streams(self) -> Union[OrderedDict, None]:
        if (stream := super()._get_streams()) is not None:
            return stream
        return self._check_vods()


__plugin__ = TwitchRewind
