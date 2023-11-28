import os


class config:
    """
    A configuration class for storing environment-specific settings.

    This class is designed to hold configuration variables that are essential
    for the application, such as tokens and keys. These variables are typically
    loaded from the environment to ensure security and flexibility across different
    deployment environments.

    Class Attributes:
        TG_BOT_TOKEN (str): Telegram Bot Token, fetched from the environment variable 'TG_BOT_TOKEN'.
                            This token is used to authenticate and interact with the Telegram Bot API.
    """

    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "PLACE HOLDER")
