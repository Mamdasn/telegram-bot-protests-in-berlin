import datetime
from functools import partial

import psycopg2


class Fetchpostgres:
    """
    A class to handle interactions with a PostgreSQL database.

    This class provides methods for connecting to, querying, and managing data in a PostgreSQL database. It includes functionality for establishing and closing database connections, storing and retrieving data, and formatting the output of queries for display.

    :param params: Parameters to establish a PostgreSQL connection.
    :type params: dict
    """

    def __init__(self, params) -> None:
        """
        Initialize the Fetchpostgres class with connection parameters for PostgreSQL.

        :param params: Parameters to establish a PostgreSQL connection.
        :type params: dict
        """
        self.params = params
        self.connection = psycopg2.connect

    def start(self):
        """
        Establish a cursor for the PostgreSQL connection.
        """
        self.cursor = self.connection.cursor()
        print("PostgreSQL connection is started")

    def close(self):
        """
        Close the cursor and the PostgreSQL connection if open.
        """
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection is closed")

    def store_client_data(self, data):
        """
        Store client data in the PostgreSQL database, creating the table if it does not exist.

        :param data: Client data to be stored.
        :type data: tuple
        :return: Commit status of the connection.
        :rtype: None
        """
        with self.connection(**self.params).cursor() as cursor:
            check_existence = """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'clients'
                );
                """
            create_command = """
                CREATE TABLE clients (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    Date BIGINT NOT NULL,
                    Message_Text VARCHAR,
                    Message_ID VARCHAR(15) NOT NULL,
                    Chat_ID VARCHAR(15) NOT NULL,
                    Chat_Type VARCHAR(10) NOT NULL,
                    UNIQUE(Date, Message_ID, Chat_ID)
                )
                """
            cursor.execute(check_existence)
            tables_exists = cursor.fetchone()[0]

            if not tables_exists:
                cursor.execute(create_command)

            (Date, Message_Text, Message_ID, Chat_ID, Chat_Type) = data
            sql_insert = """INSERT INTO clients (Date, Message_Text, Message_ID, Chat_ID, Chat_Type)
                            VALUES(%s::BIGINT, %s, %s, %s, %s) ON CONFLICT (Date, Message_ID, Chat_ID) DO UPDATE
                            SET Message_Text = EXCLUDED.Message_Text
                            RETURNING id;"""
            cursor.execute(
                sql_insert,
                (
                    Date,
                    Message_Text,
                    Message_ID,
                    Chat_ID,
                    Chat_Type,
                ),
            )
            cursor.fetchone()
        return self.connection(**self.params).commit()

    def get_by_specific_date(self, date):
        """
        Retrieve records from the PostgreSQL database by a specific date.

        :param date: The specific date to retrieve records.
        :type date: datetime.datetime
        :return: Fetched records from the database.
        :rtype: list
        """
        with self.connection(**self.params).cursor() as cursor:
            postgreSQL_select_Query = "select * from events where Datum = %s::date"
            cursor.execute(postgreSQL_select_Query, (date,))
            fetched_records = cursor.fetchall()
            return fetched_records

    def get_by_specific_time(self, column, time):
        """
        Retrieve records from the PostgreSQL database by a specific time.

        :param column: The column name to match the specific time.
        :type column: str
        :param time: The specific time to retrieve records.
        :type time: datetime.time
        :return: Fetched records from the database.
        :rtype: list
        """
        with self.connection(**self.params).cursor() as cursor:
            postgreSQL_select_Query = f"select * from events where {column} = %s::time"
            cursor.execute(postgreSQL_select_Query, (time,))
            fetched_records = cursor.fetchall()
            return fetched_records

    def get_query_column(self, column, query):
        """
        Retrieve rows from the 'events' table where the specified column contains the specified query.

        :param column: The column to be queried.
        :type column: str
        :param query: The query value to search in the column.
        :type query: str
        :return: Rows from the database where the column contains the query.
        :rtype: list
        """
        with self.connection(**self.params).cursor() as cursor:
            query_statement = f"{column} ILIKE ANY(%s)"
            cursor.execute(
                "SELECT * FROM events WHERE " + query_statement,
                ([f"%{q}%" for q in query],),
            )
            fetched_records = cursor.fetchall()
            return fetched_records

    def get_query_any_column(
        self, query, columns=["Aufzugsstrecke", "Versammlungsort", "Thema", "PLZ"]
    ):
        """
        Retrieve non-repetitive rows from the 'events' table where any of the specified columns contains the specified query.

        :param query: The query value to search in the columns.
        :type query: str
        :param columns: List of column names to search the query in, defaults to ['Aufzugsstrecke', 'Versammlungsort', 'Thema', 'PLZ'].
        :type columns: list[str], optional
        :return: Distinct rows from the database where any of the specified columns contains the query.
        :rtype: list
        """
        with self.connection(**self.params).cursor() as cursor:
            query_statement = " OR ".join([f"{column} ILIKE %s" for column in columns])
            if "Datum" in columns:
                query_statement = query_statement.replace(
                    "Datum", "TO_CHAR(Datum, 'DD.MM.YYYY')"
                )
            query_statement = " AND ".join([f"({query_statement})" for q in query])
            query_condition = [f"%{q}%" for q in query for c in columns]
            today_date = datetime.datetime.today().strftime("%Y.%m.%d")
            cursor.execute(
                f"SELECT DISTINCT ON ({', '.join(columns)}) * FROM events WHERE ((Datum >= '{today_date}') AND {query_statement})",
                query_condition,
            )
            fetched_records = cursor.fetchall()
            fetched_records.sort(key=lambda x: x[0])
            return fetched_records

    def get_von_query(self, time):
        """
        Retrieve rows from the 'events' table where the 'Von' column matches a specific time.

        :param time: The specific time to match in the 'Von' column.
        :type time: datetime.time
        :return: Rows from the database matching the specified time in the 'Von' column.
        :rtype: list
        """
        f = partial(self.get_by_specific_time, column="Von")
        return f(time=time)

    def get_bis_query(self, time):
        """
        Retrieve rows from the 'events' table where the 'Bis' column matches a specific time.

        :param time: The specific time to match in the 'Bis' column.
        :type time: datetime.time
        :return: Rows from the database matching the specified time in the 'Bis' column.
        :rtype: list
        """
        f = partial(self.get_by_specific_time, column="Bis")
        return f(time=time)

    def get_Thema_query(self, query):
        """
        Retrieve rows from the 'events' table where the 'Thema' column contains a specific query.

        :param query: The query value to search in the 'Thema' column.
        :type query: str
        :return: Rows from the database where the 'Thema' column contains the query.
        :rtype: list
        """
        f = partial(self.get_query_column, column="Thema")
        return f(query=query)

    def get_PLZ_query(self, query):
        """
        Retrieve rows from the 'events' table where the 'PLZ' column contains a specific query.

        :param query: The query value to search in the 'PLZ' column.
        :type query: str
        :return: Rows from the database where the 'PLZ' column contains the query.
        :rtype: list
        """
        f = partial(self.get_query_column, column="PLZ")
        return f(query=query[0])

    def get_Versammlungsort_query(self, query):
        """
        Retrieve rows from the 'events' table where the 'Versammlungsort' column contains a specific query.

        :param query: The query value to search in the 'Versammlungsort' column.
        :type query: str
        :return: Rows from the database where the 'Versammlungsort' column contains the query.
        :rtype: list
        """
        f = partial(self.get_query_column, column="Versammlungsort")
        return f(query=query)

    def get_Aufzugsstrecke_query(self, query):
        """
        Retrieve rows from the 'events' table where the 'Aufzugsstrecke' column contains a specific query.

        :param query: The query value to search in the 'Aufzugsstrecke' column.
        :type query: str
        :return: Rows from the database where the 'Aufzugsstrecke' column contains the query.
        :rtype: list
        """
        f = partial(self.get_query_column, column="Aufzugsstrecke")
        return f(query=query)

    @staticmethod
    def escape_special_html_characters(string):
        """
        Escape special HTML characters in a string to their corresponding HTML entities.

        This method replaces the following characters:
        - '<' with '&lt;'
        - '>' with '&gt;'
        - '&' with '&amp;'

        :param string: The input string containing special HTML characters.
        :type string: str
        :return: The string with special HTML characters replaced by their corresponding HTML entities.
        :rtype: str
        """
        return string.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def format_postgres_output(self, q):
        """
        Format the output from a PostgreSQL query for display.

        :param q: The query result to be formatted.
        :type q: tuple or str
        :return: A formatted string representation of the query result.
        :rtype: str
        """
        if isinstance(q, str):
            return q
        data = {
            "date": q[1],
            "time range start": q[2],
            "time range end": q[3],
            "thema": Fetchpostgres.escape_special_html_characters(q[4]),
            "plz": q[5],
            "versammlung": Fetchpostgres.escape_special_html_characters(q[6]),
            "location": q[7],
        }
        newline = "\n"
        date = f'<b>On {data["date"].strftime("%d.%m.%Y")}</b>' if data["date"] else ""
        time_range = (
            f'{data["time range start"].strftime("%H:%M")} to {data["time range end"].strftime("%H:%M:")}'
            if data["time range end"]
            else f'{data["time range start"].strftime("%H:%M")}'
            if data["time range start"]
            else ""
        )
        thema = f"<b>Thema</b>: {data['thema']}{newline}" if data["thema"] else ""
        plz = (
            f"<b>PLZ</b>: {data['plz']}{newline}"
            if ((data["plz"] != "") and (data["plz"] != "00000"))
            else ""
        )
        google_maps_url_base = "https://www.google.com/maps/search/?api=1&query="
        google_maps_url = (
            f"{google_maps_url_base}{data['versammlung']} {data['plz']} Berlin"
            if ((data["plz"] != "") and (data["plz"] != "00000"))
            else f"{google_maps_url_base}{data['versammlung']} Berlin"
        )
        versammlungsort = (
            f'<b>Versammlungsort</b>: <a href="{google_maps_url}">{data["versammlung"]}{newline}</a>'
            if data["versammlung"]
            else ""
        )
        route_with_google_maps_urls = ""
        if data["location"]:
            find_indexes = [
                data["location"].find(sep)
                for sep in [" - ", "/"]
                if data["location"].find(sep) != -1
            ]
            if find_indexes:
                first_location_index = min(find_indexes)
                first_location = data["location"][:first_location_index]
                route_with_google_maps_urls = f'<a href="{google_maps_url_base}{first_location} Berlin">{first_location}</a>{data["location"][first_location_index:]}'
            else:
                first_location = data["location"]
                route_with_google_maps_urls = f'<a href="{google_maps_url_base}{first_location} Berlin">{first_location}</a>'
        aufzugsstrecke = (
            f"<b>Aufzugsstrecke</b>: {route_with_google_maps_urls}{newline}"
            if data["location"]
            else ""
        )
        # return f"<b>id: {q[0]}</b>{newline}{date}{' - ' if date and time_range else ''}{time_range}{newline}{thema}{plz}{versammlungsort}{aufzugsstrecke}"
        return f"▪️{date}{' - ' if date and time_range else ''}{time_range}{newline}{thema}{plz}{versammlungsort}{aufzugsstrecke}"

    def format_postgre_queries(self, queries):
        """
        Format multiple PostgreSQL query results for display.

        :param queries: A list of query results to be formatted.
        :type queries: list
        :return: A list of formatted string representations of the query results.
        :rtype: list
        """
        return [self.format_postgres_output(q) for q in queries]
