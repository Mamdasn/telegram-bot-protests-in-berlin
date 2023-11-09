import psycopg2
from postgresconf.config import config
from functools import partial
import datetime
import urllib.parse


class Fetchpostgres:
    def __init__(self, params) -> None:
        self.params = params
        self.connection = psycopg2.connect

    def start(self):
        self.cursor = self.connection.cursor()
        print("PostgreSQL connection is started")

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection is closed")

    def getBySpecificDate(self, date):
        with self.connection(**self.params).cursor() as cursor:
            postgreSQL_select_Query = "select * from events where Datum = %s::date"
            cursor.execute(postgreSQL_select_Query, (date,))
            fetched_records = cursor.fetchall()
            return fetched_records

    def getBySpecificTime(self, column, time):
        with self.connection(**self.params).cursor() as cursor:
            postgreSQL_select_Query = f"select * from events where {column} = %s::time"
            cursor.execute(postgreSQL_select_Query, (time,))
            fetched_records = cursor.fetchall()
            return fetched_records

    def get_query_column(self, column, query):
        """
        Retrieve rows from the 'events' table where the specified column contains the specified query.
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

    def getVonQuery(self, time):
        f = partial(self.getBySpecificTime, column="Von")
        return f(time=time)

    def getBisQuery(self, time):
        f = partial(self.getBySpecificTime, column="Bis")
        return f(time=time)

    def getThemaQuery(self, query):
        f = partial(self.get_query_column, column="Thema")
        return f(query=query)

    def getPLZQuery(self, query):
        f = partial(self.get_query_column, column="PLZ")
        return f(query=query[0])

    def getVersammlungsortQuery(self, query):
        f = partial(self.get_query_column, column="Versammlungsort")
        return f(query=query)

    def getAufzugsstreckeQuery(self, query):
        f = partial(self.get_query_column, column="Aufzugsstrecke")
        return f(query=query)

    def format_postgres_output(self, q):
        if type(q) == str:
            return q
        newline = "\n"
        date = f'<b>On {q[1].strftime("%d.%m.%Y")}</b>' if q[1] else ""
        time_range = (
            f'{q[2].strftime("%H:%M")} to {q[3].strftime("%H:%M:")}'
            if q[3]
            else f'{q[2].strftime("%H:%M")}'
            if q[2]
            else ""
        )
        thema = f"<b>Thema</b>: {q[4]}{newline}" if q[4] else ""
        plz = f"<b>PLZ</b>: {q[5]}{newline}" if q[5] else ""
        google_maps_url_base = "https://www.google.com/maps/search/?api=1&query="
        google_maps_url = f"{google_maps_url_base}{q[6]} {q[5]} Berlin"
        versammlungsort = (
            f'<b>Versammlungsort</b>: <a href="{google_maps_url}">{q[6]}{newline}</a>'
            if q[6]
            else ""
        )
        route_with_google_maps_urls = ""
        if q[7]:
            find_indexes = [
                q[7].find(sep) for sep in [" - ", "/"] if q[7].find(sep) != -1
            ]
            if find_indexes:
                first_location_index = min(find_indexes)
                first_location = q[7][:first_location_index]
                route_with_google_maps_urls = f'<a href="{google_maps_url_base}{first_location} Berlin">{first_location}</a>{q[7][first_location_index:]}'
            else:
                first_location = q[7]
                route_with_google_maps_urls = f'<a href="{google_maps_url_base}{first_location} Berlin">{first_location}</a>'
        aufzugsstrecke = (
            f"<b>Aufzugsstrecke</b>: {route_with_google_maps_urls}{newline}"
            if q[7]
            else ""
        )
        # return f"<b>id: {q[0]}</b>{newline}{date}{' - ' if date and time_range else ''}{time_range}{newline}{thema}{plz}{versammlungsort}{aufzugsstrecke}"
        return f"▪️{date}{' - ' if date and time_range else ''}{time_range}{newline}{thema}{plz}{versammlungsort}{aufzugsstrecke}"

    def format_postgre_queries(self, queries):
        return [self.format_postgres_output(q) for q in queries]
