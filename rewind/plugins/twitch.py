import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, OrderedDict, Union

from requests import HTTPError
from streamlink.plugin import PluginArgument, PluginArguments, PluginError
from streamlink.plugins.twitch import Twitch
from tabulate import tabulate


class TwitchVOD:

    def __init__(self, data: dict) -> None:
        self.data = data
        self._streams = OrderedDict()
        self._index = 1

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value) -> int:
        self._index = value
        return self.index

    @property
    def has_streams(self) -> bool:
        return len(self._streams) >= 1

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
    def identifier(self) -> str:
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
        return self._parse_date_str(created).strftime("%Y-%m-%d")

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

    # pylint: disable=unnecessary-comprehension
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

    @staticmethod
    def clamp(value: int, lower: int, upper: int) -> int:
        return max(upper, min(lower, value))

    @staticmethod
    def get_int_from_user(prompt: str = None) -> int:
        while True:
            try:
                raw = input(prompt)
                if raw == "":
                    continue
                return int(raw)
            except ValueError:
                print("That doesn't look like a number...")
                continue

    def _parse_video_data(self, response: dict) -> List[TwitchVOD]:
        vods, idx = [], 1
        for data in response.get("videos", []):
            vod = TwitchVOD(data)
            if not vod.has_streams:
                self._fill_vod_stream(vod)
            vod.index = idx
            vods.append(vod)
            idx += 1
        return sorted(vods, key=lambda vod: vod.date, reverse=True)

    def _fill_vod_stream(self, vod: TwitchVOD) -> None:
        tmp = self.video_id

        try:
            self.video_id = vod.identifier
            vod.streams = self._get_hls_streams_video()
        except PluginError:
            pass
        finally:
            self.video_id = tmp

    def _get_vods(self) -> List[TwitchVOD]:
        res = self._get_videos(broadcast_type="archive")
        return self._parse_video_data(res)

    def _get_videos(self, **kwargs) -> dict:
        return self.api.call(
            f"/kraken/channels/{self.channel_id}/videos",
            **kwargs
        )

    # pylint: disable=unsubscriptable-object
    def _check_vods(self) -> Union[OrderedDict, None]:
        self.logger.info(f"{self.channel} is not currently streaming...")

        if not self.options.get("check_vods"):
            return None

        self.logger.info("Checking for past broadcasts now")

        try:
            vods = list(self._get_vods())
        except (PluginError, HTTPError) as ex:
            self.logger.error(f"Could not get past broadcasts: {ex}")
            return None

        if len(vods) == 0:
            self.logger.info(f"{self.channel} has no past broadcasts")
            return None

        if self.options.get("pick_most_recent_vod"):
            for vod in vods:
                if vod.has_streams:
                    self.logger.info("Loading most recent past broadcast now")
                    return vod.streams

        _map = {
            "#": "index",
            "ID": "identifier",
            "Game": "game",
            "Date": "date",
            "Length": "length",
            "Title": "title"
        }

        self.print_tab_vod_info(vods, _map)

        choice = self.get_int_from_user(prompt="Pick a VOD: ")

        vod = vods[self.clamp(choice, len(vods), 1) - 1]
        if vod.has_streams:
            return vod.streams

        return None

    # pylint: disable=unsubscriptable-object
    def _get_streams(self) -> Union[OrderedDict, None]:
        streams = super()._get_streams()
        if streams is not None:
            return streams
        return self._check_vods()

    def print_tab_vod_info(
        self,
        vod_list: List[TwitchVOD],
        header_attrib_map: Dict,
        ignore_missing: bool = True
    ) -> None:
        vlist = list(filter(lambda v: v.has_streams, vod_list))

        if len(vlist) == 0:
            return

        tabular_data = []
        for vod in vlist:
            data = []
            for attrib in header_attrib_map.values():
                if not hasattr(vod, attrib):
                    self.logger.warning(
                        f"{vod} does not have attribute {attrib}"
                    )
                    if not ignore_missing:
                        continue
                data.append(getattr(vod, attrib, None))
            tabular_data.append(data)

        headers = header_attrib_map.keys()
        self.logger.info("\n" + tabulate(tabular_data, headers))


# pylint: disable=invalid-name
__plugin__ = TwitchRewind
