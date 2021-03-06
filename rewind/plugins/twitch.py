from streamlink.plugin import PluginArgument, PluginArguments
from streamlink.plugins.twitch import Twitch


class TwitchRewind(Twitch):

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
            "vod-check-limit",
            default=10,
            help="""
            Limit VODs to X most recent
            """
        )
    )

__plugin__ = TwitchRewind
