from streamlink_cli import main
from streamlink_cli.console import ConsoleUserInputRequester

from rewind.client import Client


def patched_streamlink_setup():
    cir = ConsoleUserInputRequester(main.console)
    main.streamlink = Client({"user-input-requester": cir})


def run():
    main.setup_streamlink = patched_streamlink_setup
    print("fucdk")
    main.main()
