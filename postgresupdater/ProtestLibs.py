from requests import Session
from bs4 import BeautifulSoup
import psycopg2
from postgresconf.config import config
from time import sleep


class ProtestGrabber:
    def get_protest_list(url):
        with Session() as session:
            req = session.get(url)
            if req.status_code != 200:
                raise ValueError("It seems like there is a problem with internet connection. Please check your internet connection and try again!")
            content = req.content
            parsed_content = BeautifulSoup(content, 'html.parser')
            tabel_of_content = parsed_content.find('div', {'id':'results'})
            protests = tabel_of_content.find('tbody').find_all("tr", {"class": True})

            return protests

    def parse_protest_list(event):
        try:
            Datum           = event.find('td', {'headers': 'Datum'}).get_text().strip()
            Von             = event.find('td', {'headers': 'Von'}).get_text().strip()
            Bis             = event.find('td', {'headers': 'Bis'}).get_text().strip()
            Thema           = event.find('td', {'headers': 'Thema'}).get_text().strip()
            PLZ             = event.find('td', {'headers': 'PLZ'}).get_text().strip()
            Versammlungsort = event.find('td', {'headers': 'Versammlungsort'}).get_text().strip()
            Aufzugsstrecke  = event.find('td', {'headers': 'Aufzugsstrecke'}).get_text().strip()

            Datum = '.'.join(Datum.split('.')[::-1])

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
    def write_to_database(data):

        """create tables in the PostgreSQL database and insert data into it"""

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
            insert a new event into the events table
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
            print('Waiting for postgres to load.')            
            for _ in range(5):
                try:
                    conn = psycopg2.connect(**params)
                except Exception as e:
                    print(e)
                sleep(5)
                print('.', end='')
            else:
                print()
                
            print('The connection with the database is established at last.')

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

