import os


class config:
    """
    A configuration class for reading environment-specific settings.

    This class is designed to hold configuration variables that are essential
    for the application, such as tokens and keys. These variables are typically
    loaded from the environment to ensure security and flexibility across different
    deployment environments.

    Class Attributes:
        DB_UPDATE_PERIOD (int): Database Update Period, fetched from the environment variable 'DB_UPDATE_PERIOD'.
                                This variable sets the time period of updating the database, defaulting to 3600 seconds
                                if the environment variable is not set or invalid.
        POSTGRES_HOST (str): Host of the postgres server.
        POSTGRES_USER (str): The postgres user used to login to the server.
        POSTGRES_PASSWORD (str): The postgres password used to login to the server.
        POSTGRES_DB (str): The postgres database name.


    Static Methods:
        _isinteger(text, default): Converts the input text to an integer. If the conversion fails, returns the default value.
                                   This method is used internally to ensure environment variables are correctly interpreted
                                   as integers.
    """

    @staticmethod
    def _isinteger(text, default):
        try:
            return int(text)
        except Exception:
            return default

    DB_UPDATE_PERIOD = _isinteger(os.environ.get("DB_UPDATE_PERIOD"), default=3600)
    POSTGRES = {
        "host": os.environ.get("POSTGRES_HOST", "PLACE HOLDER"),
        "database": os.environ.get("POSTGRES_DB", "PLACE HOLDER"),
        "user": os.environ.get("POSTGRES_USER", "PLACE HOLDER"),
        "password": os.environ.get("POSTGRES_PASSWORD", "PLACE HOLDER"),
    }
