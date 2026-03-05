import asyncio
import logging
import re
import socket
from contextlib import contextmanager
from time import sleep
from typing import Iterator
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import aiohttp
import psycopg2
from aiohttp import ClientResponse
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class ProtestGrabber:
    """
    A class dedicated to fetching and parsing protest information from web pages.

    Leverages `aiohttp` for asynchronous web requests and `BeautifulSoup` for HTML parsing.

    :param aiohttp.ClientSession session: A session object for making asynchronous HTTP requests.
    """

    def __init__(self, CRAWLER_UA_UNIQ_ID=1234567890):
        self.CRAWLER_UA = f"BerlinProtests/{CRAWLER_UA_UNIQ_ID}"
        self.ROBOT_TXT_ALLOWS = False

    async def fetch_content(
        self, url: str, retry: int = 10, delay: int = 20, allow_404: bool = False
    ) -> ClientResponse:
        """
        Fetches HTML content from a URL asynchronously, with retry logic for robustness.

        :param url: The URL to fetch the content from.
        :param retry: Maximum number of retries on fetch failure.
        :param delay: Delay between retries in seconds.
        :return: The HTML content of the page as a string.
        :raises Exception: If all retries fail.
        """

        async with aiohttp.ClientSession(
            headers={"User-Agent": self.CRAWLER_UA}
        ) as session:
            while retry > 0:
                try:
                    proxy = "http://tor_privoxy:8118"
                    async with session.get(url, proxy=proxy) as response:
                        if allow_404 and response.status == 404:
                            return "" # if the url path doesn't exist: e.g. when robot.txt is removed
                        response.raise_for_status()
                        return await response.text()

                except Exception as e:
                    logger.error(
                        f"Retry {retry}: Exception occurred: {e}. Retrying after {delay} seconds..."
                    )
                    retry -= 1
                    if retry == 0:
                        break
                    try:
                        ProtestGrabber.rotate_ip_request()
                    except Exception as rotate_error:
                        logger.warning(f"Could not rotate Tor IP: {rotate_error}")
                    await asyncio.sleep(delay)
        return None

    async def check_robot_txt_rules(self, url: str) -> bool:
        """
        Check robots.txt to see if a crawler is allowed to fetch the given URL.

        :param url: The URL to scrape for protest information.

        :return: Bool that is True if allowed, False if disallowed.
        """
        url_parsed = urlparse(url)
        url_robot_txt = f"{url_parsed.scheme}://{url_parsed.netloc}/robots.txt"
        robots_txt = await self.fetch_content(url_robot_txt, allow_404=True)
        if robots_txt is None:
            logger.warning("Could not retrieve robots.txt;")
            self.ROBOT_TXT_ALLOWS = True
            return self.ROBOT_TXT_ALLOWS
        lines = robots_txt.splitlines()
        rp = RobotFileParser()
        rp.parse(lines)
        if not rp.can_fetch(self.CRAWLER_UA, url):
            logger.warning("Access to this URL is disallowed by robots.txt")
            self.ROBOT_TXT_ALLOWS = False
        else:
            logger.info("Access to this URL is allowed by robots.txt")
            self.ROBOT_TXT_ALLOWS = True
        return self.ROBOT_TXT_ALLOWS

    async def get_protest_list(self, url: str) -> list:
        """
        Retrieves a list of protest events by parsing HTML content from the specified URL.

        :param url: The URL to scrape for protest information.
        :return: A list of BeautifulSoup Tag objects, each representing a protest event.
        """
        logger.info(f"url: {url}")

        if self.ROBOT_TXT_ALLOWS is False:
            await self.check_robot_txt_rules(url)

        if self.ROBOT_TXT_ALLOWS:
            html_content = await self.fetch_content(url)
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")
                table_of_content = soup.find("div", {"id": "searchresults"})
                if table_of_content:
                    protests = table_of_content.find("tbody").find_all(
                        "tr", class_=True
                    )
                    return protests
        return []

    @staticmethod
    def rotate_ip_request() -> bool:
        """
        Send a request to torprivoxy to change the ip.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("tor_privoxy", 9051))
            commands = 'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT\r\n'
            s.sendall(commands.encode("utf-8"))

            data = s.recv(1024)
            if data.decode("utf-8").find("OK") != -1:
                return True
            else:
                return False

    @staticmethod
    def parse_protest_list(event: Tag) -> dict:
        """
        Extracts details from an HTML segment representing a single protest event.

        :param event: The BeautifulSoup Tag object to parse.
        :return: A dictionary containing details of the protest event.
        """

        def get_text(soup):
            if soup:
                text = soup.get_text(strip=True)
                return text or None
            else:
                return None

        def extract_versammlungsort_from_route(route: str | None) -> str | None:
            if not route:
                return None

            cleaned_route = re.sub(
                r"^\s*(?:neu|alt)\s*:\s*", "", route, flags=re.IGNORECASE
            ).strip()
            if not cleaned_route:
                return None

            clear_separator_pattern = r"(?:\s+[–—-]\s*(?:>\s*)?|[–—-]\s+(?:>\s*)?)"
            route_parts = [
                part.strip()
                for part in re.split(clear_separator_pattern, cleaned_route)
                if part.strip()
            ]


            if len(route_parts) <= 1 and re.search(r"\S[–—-]\S", cleaned_route):
                route_parts = [
                    part.strip() for part in re.split(r"[–—-]", cleaned_route) if part.strip()
                ]

            parts = route_parts
            if not parts:
                return None

            candidate = parts[0]
            for part in parts[1:]:
                if len(candidate) > 5:
                    break
                candidate = f"{candidate}-{part}"

            return candidate or None

        try:
            details = {
                "Datum": get_text(event.find("td", {"headers": "Datum"})),
                "Von": get_text(event.find("td", {"headers": "Von"})),
                "Bis": get_text(event.find("td", {"headers": "Bis"})),
                "Thema": get_text(event.find("td", {"headers": "Thema"})),
                "PLZ": get_text(event.find("td", {"headers": "PLZ"})),
                "Versammlungsort": get_text(
                    event.find("td", {"headers": "Versammlungsort"})
                ),
                "Aufzugsstrecke": get_text(
                    event.find("td", {"headers": "Aufzugsstrecke"})
                ),
            }

            if not details["Versammlungsort"]:
                details["Versammlungsort"] = extract_versammlungsort_from_route(details["Aufzugsstrecke"])

            all_values_are_none = all([v is None for v in details.values()])
            if all_values_are_none:
                return {}

            # Adjusting date format if needed
            if details.get("Datum"):
                details["Datum"] = ".".join(details["Datum"].split(".")[::-1])

            return details
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return {}


class ProtestPostgres:
    """
    Manages the storage of protest information in a PostgreSQL database.

    :param dict db_config: Configuration parameters for connecting to the database.
    """

    def __init__(self, db_config):
        """
        Initializes the database configuration.

        :param db_config: Database connection parameters.
        :type db_config: dict
        """
        self.db_config = db_config

    @contextmanager
    def _db_cursor(self) -> psycopg2.extensions.connection:
        """
        Establishes a connection to the PostgreSQL database.

        :return: A psycopg2 connection object.
        """
        logger.info("Waiting for postgres to load.")
        retry = 60
        while retry > 0:
            try:
                connection = psycopg2.connect(**self.db_config)
                cursor = connection.cursor()
                break

            except Exception as e:
                logger.error(e)
                if retry == 1:
                    raise e
                retry -= 1

            sleep(5)

        logger.info("Established connection to database.")

        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(
                "Commit resulted in error. Rolling back to the privious commit!"
            )
            raise e
        finally:
            connection.close()

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
        with self._db_cursor() as cursor:
            cursor.execute(create_command)

        return True

    def _insert_event(self, cursor: psycopg2.extensions.cursor, data: dict) -> bool:
        """
        Inserts a new event into the 'events' table.

        :param cursor: The database cursor for executing SQL commands.
        :type cursor: psycopg2.extensions.cursor
        :param data: contain event data
        :type data: dict
        """

        sql_protest = """INSERT INTO events (Datum, Von, Bis, Thema, PLZ, Versammlungsort, Aufzugsstrecke)
                            VALUES(%s::DATE, %s::TIME, %s::TIME, %s, %s, %s, %s) ON CONFLICT (PLZ, Versammlungsort, Datum, Von) DO UPDATE
                            SET Aufzugsstrecke = EXCLUDED.Aufzugsstrecke, Thema = EXCLUDED.Thema, Bis = EXCLUDED.Bis
                            RETURNING id;"""

        cursor.execute(sql_protest, list(data.values()))

        return True

    def write_to_database(self, data: Iterator[str]) -> bool:
        """
        Writes a list of protest event data into the 'events' table.

        :param data: A list of dictionaries, each representing protest event data.
        :type data: list of dict
        :return: True if the operation was successful, False otherwise.
        """
        try:
            self._ensure_table_exists()
            with self._db_cursor() as cursor:
                for event in data:
                    if not event:
                        continue
                    missing_required_field = False
                    for field in ("Datum", "Von", "Bis", "PLZ", "Versammlungsort"):
                        if not str(event.get(field) or "").strip():
                            logger.warning(f"Skipping event without {field}.")
                            missing_required_field = True
                            break
                    if missing_required_field:
                        continue
                    self._insert_event(cursor, event)
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Could not write data into database due to: {error}")
            return False
