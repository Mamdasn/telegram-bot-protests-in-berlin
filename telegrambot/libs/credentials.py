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
        POSTGRES_HOST (str): Host of the postgres server.
        POSTGRES_USER (str): The postgres user used to login to the server.
        POSTGRES_PASSWORD (str): The postgres password used to login to the server.
        POSTGRES_DB (str): The postgres database name.
    """

    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "PLACE HOLDER")
    POSTGRES = {
            'host': os.environ.get("POSTGRES_HOST", "PLACE HOLDER"), 
            'database': os.environ.get("POSTGRES_DB", "PLACE HOLDER"), 
            'user': os.environ.get("POSTGRES_USER", "PLACE HOLDER"), 
            'password': os.environ.get("POSTGRES_PASSWORD", "PLACE HOLDER")
            }

