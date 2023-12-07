from requests import Session
from bs4 import BeautifulSoup
import psycopg2
from postgresconf.config import config
from time import sleep


class ProtestGrabber:
    """
    A class for grabbing and parsing protest information from a specified URL.

    This class contains methods for fetching protest event data from a webpage and parsing the HTML content to extract relevant information about each protest event.

    Methods:
        | get_protest_list(url): Fetches the list of protests from a given URL and parses the HTML to extract protest data.
        | parse_protest_list(event): Parses individual protest event data from the HTML content of a webpage.

    The class relies on the `requests` and `BeautifulSoup` libraries for fetching and parsing web content, respectively.
    """

    def get_protest_list(url):
        """
        Fetches the list of protests from the specified URL and returns a BeautifulSoup object containing the parsed protest data.

        :param url: The URL to fetch the protest information from.
        :type url: str

        :return: A list of BeautifulSoup objects, each representing a protest event.
        :rtype: list of bs4.element.Tag

        :raises ValueError: If there's an issue with the internet connection or the request to the URL fails.
        """
        with Session() as session:
            req = session.get(url)
            print("This is the status code:", req.status_code)
            if not req.status_code in [200, 418]:
                raise ValueError(
                    "It seems like there is a problem with internet connection. Please check your internet connection and try again!"
                )
            if req.status_code != 200:
                print(f"The request status code is {req.status_code}, now relaying to a proxy configuration...")
                proxies = {
                        'http': 'http://0.0.0.0:8118',
                        'https': 'https://0.0.0.0:8118'
                    }
                req = session.get(url, proxies=proxies)
            content = req.content
            if content:
                parsed_content = BeautifulSoup(content, "html.parser")
                tabel_of_content = parsed_content.find("div", {"id": "results"})
                protests = tabel_of_content.find("tbody").find_all("tr", {"class": True})
                return protests
            else:
                print(f"With the status_code: {req.status_code}, the page respond content is empty.")
                return None

    def parse_protest_list(event):
        """
        Parses an individual protest event's HTML content and extracts relevant details.

        :param event: A BeautifulSoup object representing an individual protest event.
        :type event: bs4.element.Tag

        :return: A dictionary with parsed data of the protest event or False if parsing fails.
        :rtype: dict or bool

        The function attempts to extract details such as date, time, theme, postal code, and location of the protest. In case of an error during parsing, it returns False.
        """
        try:
            Datum = event.find("td", {"headers": "Datum"}).get_text().strip()
            Von = event.find("td", {"headers": "Von"}).get_text().strip()
            Bis = event.find("td", {"headers": "Bis"}).get_text().strip()
            Thema = event.find("td", {"headers": "Thema"}).get_text().strip()
            PLZ = event.find("td", {"headers": "PLZ"}).get_text().strip()
            Versammlungsort = (
                event.find("td", {"headers": "Versammlungsort"}).get_text().strip()
            )
            Aufzugsstrecke = (
                event.find("td", {"headers": "Aufzugsstrecke"}).get_text().strip()
            )

            Datum = ".".join(Datum.split(".")[::-1])

            return {
                "Datum": Datum,
                "Von": Von,
                "Bis": Bis,
                "Thema": Thema,
                "PLZ": PLZ,
                "Versammlungsort": Versammlungsort,
                "Aufzugsstrecke": Aufzugsstrecke,
            }
        except:
            return False


class ProtestPostgres:
    """
    A class for handling the storage of protest information into a PostgreSQL database.

    This class includes methods for creating the necessary database table and inserting protest data into it. It interacts with a PostgreSQL database using the psycopg2 library.

    Methods:
        | write_to_database(data): Creates the 'events' table if it doesn't exist and writes protest data to the database.
        | _insert_event(...): A helper method for inserting a single event into the database.
    """

    def write_to_database(data):
        """
        Creates the 'events' table in the PostgreSQL database and inserts the given data into it.

        This method checks for the existence of the 'events' table, creates it if necessary, and then proceeds to insert the provided data into the table.

        :param data: A list of dictionaries, each containing data about a protest event to be inserted into the database.
        :type data: list of dict

        :return: True if the operation is successful, False otherwise.
        :rtype: bool

        :raises Exception: If any error occurs during database connection or operation.

        The method utilizes a nested function `_insert_event` to handle the insertion of each individual event.
        """

        def _insert_event(
            cursor,
            Datum=None,
            Von=None,
            Bis=None,
            Thema=None,
            PLZ=None,
            Versammlungsort=None,
            Aufzugsstrecke=None,
        ):
            """
            Inserts a new event into the 'events' table.

            This helper function is used by 'write_to_database' to insert individual protest events into the database.

            :param cursor: The database cursor to execute the query.
            :type cursor: psycopg2.extensions.cursor
            :param Datum: Date of the event.
            :type Datum: str, optional
            :param Von: Start time of the event.
            :type Von: str, optional
            :param Bis: End time of the event.
            :type Bis: str, optional
            :param Thema: Theme or topic of the event.
            :type Thema: str, optional
            :param PLZ: Postal code of the event location.
            :type PLZ: str, optional
            :param Versammlungsort: Assembly location of the event.
            :type Versammlungsort: str, optional
            :param Aufzugsstrecke: Route of the protest march.
            :type Aufzugsstrecke: str, optional

            :return: The ID of the inserted event.
            :rtype: int

            The function executes an SQL command to insert the event data, handling conflicts by updating existing records.
            """

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
            id_protest = cursor.fetchone()

        check_existence = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'events'
            );
            """
        # Datum, Von, Bis, Thema, PLZ, Versammlungsort, Aufzugsstrecke
        create_command = """
            CREATE TABLE events (
                id BIGSERIAL NOT NULL PRIMARY KEY,
                Datum DATE NOT NULL,
                Von TIME NOT NULL,
                Bis TIME NOT NULL,
                Thema VARCHAR,
                PLZ VARCHAR(10) NOT NULL,
                Versammlungsort VARCHAR(100) NOT NULL,
                Aufzugsstrecke VARCHAR,
                UNIQUE(PLZ, Versammlungsort, Datum, Von)
            )
            """

        try:
            # read the connection parameters from config file
            params = config()
            print("Waiting for postgres to load.")
            for _ in range(5):
                try:
                    conn = psycopg2.connect(**params)
                except Exception as e:
                    print(e)
                sleep(5)
                print(".", end="")
            else:
                print()

            print("The connection with the database is established at last.")

            cursor = conn.cursor()
            # check existence of tables
            cursor.execute(check_existence)
            tables_exists = cursor.fetchone()[0]

            if not tables_exists:
                # create the event table
                cursor.execute(create_command)

            for d in data:
                if d != False:
                    _insert_event(cursor=cursor, **d)

            cursor.close()
            conn.commit()
            if conn is not None:
                conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return False
        return True
