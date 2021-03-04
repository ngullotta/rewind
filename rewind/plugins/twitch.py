from streamlink.plugin import PluginArgument, plugin
from streamlink.plugins.twitch import Twitch


class TwitchRewind(Twitch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for arg in [
            PluginArgument(
                "check-vods",
                action="store_true",
                help="""
                Check for VODs (Videos On Demand) if the selected streamer is
                notcurrently streaming.
                """
            ),
            PluginArgument(
                "vod-check-limit",
                action="store_true",
                default=10,
                help="""
                Limit VODs to X most recent
                """
            )
        ]:
            self.arguments.arguments[arg.name] = arg

__plugin__ = TwitchRewind
