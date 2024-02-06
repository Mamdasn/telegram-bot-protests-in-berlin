from time import sleep

import aiohttp
import psycopg2
from aiohttp import ClientResponse
from bs4 import BeautifulSoup, Tag
from postgresconf.config import config


class ProtestGrabber:
    """
    A class dedicated to fetching and parsing protest information from web pages.

    Leverages `aiohttp` for asynchronous web requests and `BeautifulSoup` for HTML parsing.

    :param aiohttp.ClientSession session: A session object for making asynchronous HTTP requests.
    """

    async def fetch_content(
        self, url: str, retry: int = 10, delay: int = 5
    ) -> ClientResponse:
        """
        Fetches HTML content from a URL asynchronously, with retry logic for robustness.

        :param url: The URL to fetch the content from.
        :param retry: Maximum number of retries on fetch failure.
        :param delay: Delay between retries in seconds.
        :return: The HTML content of the page as a string.
        :raises Exception: If all retries fail.
        """
        async with aiohttp.ClientSession() as session:
            while retry > 0:
                try:
                    response = await session.get(url)
                    if response.status == 200:
                        return await response.text()
                    else:
                        proxies = {
                            "http": "http://tor_privoxy:8118",
                            "https": "http://tor_privoxy:8118",
                        }
                        return await session.get(url, proxies=proxies)

                except Exception as e:
                    print(
                        f"Retry {retry}: Exception occurred: {e}. Retrying after {delay} seconds..."
                    )
                    retry -= 1
                    sleep(delay)
        return None

    async def get_protest_list(self, url: str) -> list:
        """
        Retrieves a list of protest events by parsing HTML content from the specified URL.

        :param url: The URL to scrape for protest information.
        :return: A list of BeautifulSoup Tag objects, each representing a protest event.
        """
        print("url:", url)
        html_content = await self.fetch_content(url)
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            table_of_content = soup.find("div", {"id": "results"})
            if table_of_content:
                protests = table_of_content.find("tbody").find_all("tr", class_=True)
                return protests
        return []

    @staticmethod
    def parse_protest_list(event: Tag) -> dict:
        """
        Extracts details from an HTML segment representing a single protest event.

        :param event: The BeautifulSoup Tag object to parse.
        :return: A dictionary containing details of the protest event.
        """

        def get_text(soup):
            if soup:
                return soup.get_text(strip=True)
            else:
                return None

        try:
            details = {
                "Datum": get_text(event.find("td", {"headers": "Datum"})),
                "Von": get_text(event.find("td", {"headers": "Von"})),
                "Bis": get_text(event.find("td", {"headers": "Bis"})),
                "Thema": get_text(event.find("td", {"headers": "Thema"})),
                "PLZ": get_text(event.find("td", {"headers": "PLZ"})) or "00000",
                "Versammlungsort": get_text(
                    event.find("td", {"headers": "Versammlungsort"})
                ),
                "Aufzugsstrecke": get_text(
                    event.find("td", {"headers": "Aufzugsstrecke"})
                ),
            }

            # Adjusting date format if needed
            if details.get("Datum"):
                details["Datum"] = ".".join(details["Datum"].split(".")[::-1])

            # Handle missing 'Versammlungsort'
            if ("Versammlungsort" not in details) and ("Aufzugsstrecke" in details):
                details["Versammlungsort"] = (
                    details["Aufzugsstrecke"].split(" - ")[0].split(" , ")[0]
                )

            return details
        except Exception as e:
            print(f"Error parsing event: {e}")
            return {}


class ProtestPostgres:
    """
    Manages the storage of protest information in a PostgreSQL database.

    :param dict db_config: Configuration parameters for connecting to the database.
    """

    def __init__(self, db_config=config()):
        """
        Initializes the database configuration.

        :param db_config: Database connection parameters.
        :type db_config: dict
        """
        self.db_config = db_config

    def _connect(self) -> psycopg2.extensions.connection:
        """
        Establishes a connection to the PostgreSQL database.

        :return: A psycopg2 connection object.
        """
        return psycopg2.connect(**self.db_config)

    def _ensure_table_exists(self) -> bool:
        """
        Ensures the 'events' table exists in the PostgreSQL database.
        """
        create_command = """
        CREATE TABLE IF NOT EXISTS events (
            id BIGSERIAL NOT NULL PRIMARY KEY,
            Datum DATE NOT NULL,
            Von TIME NOT NULL,
            Bis TIME NOT NULL,
            Thema VARCHAR,
            PLZ VARCHAR(10) NOT NULL,
            Versammlungsort VARCHAR NOT NULL,
            Aufzugsstrecke VARCHAR,
            UNIQUE(PLZ, Versammlungsort, Datum, Von)
        );
        """
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_command)
            conn.commit()

        return True

    def _insert_event(
        self,
        cursor: psycopg2.extensions.cursor,
        Datum=None,
        Von=None,
        Bis=None,
        Thema=None,
        PLZ=None,
        Versammlungsort=None,
        Aufzugsstrecke=None,
    ) -> bool:
        """
        Inserts a new event into the 'events' table.

        :param cursor: The database cursor for executing SQL commands.
        :type cursor: psycopg2.extensions.cursor
        :param event_data: Keyword arguments containing event data fields.
        """

        all_values_are_none = (
            Datum and Von and Bis and PLZ and Versammlungsort
        ) is None
        if all_values_are_none:
            return all_values_are_none

        sql_protest = """INSERT INTO events (Datum, Von, Bis, Thema, PLZ, Versammlungsort, Aufzugsstrecke)
                            VALUES(%s::DATE, %s::TIME, %s::TIME, %s, %s, %s, %s) ON CONFLICT (PLZ, Versammlungsort, Datum, Von) DO UPDATE
                            SET Aufzugsstrecke = EXCLUDED.Aufzugsstrecke, Thema = EXCLUDED.Thema, Bis = EXCLUDED.Bis
                            RETURNING id;"""

        cursor.execute(
            sql_protest,
            (
                Datum,
                Von,
                Bis,
                Thema,
                PLZ,
                Versammlungsort,
                Aufzugsstrecke,
            ),
        )

        return True

    def write_to_database(self, data: list) -> bool:
        """
        Writes a list of protest event data into the 'events' table.

        :param data: A list of dictionaries, each representing protest event data.
        :type data: list of dict
        :return: True if the operation was successful, False otherwise.
        """
        try:
            self._ensure_table_exists()
            with self._connect() as conn:
                with conn.cursor() as cursor:
                    for event in data:
                        print(event)
                        self._insert_event(cursor, **event)
                conn.commit()
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return False
