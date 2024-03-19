import asyncio
import threading
from datetime import datetime
from queue import Queue
from time import sleep

from postgresconf import config
from ProtestLibs import ProtestGrabber, ProtestPostgres


class EventCrawler:
    """
    Crawls and processes events from specified URLs.

    This class is designed for crawling event data from various websites, parsing the obtained information, and, optionally, storing it in a database. It is capable of handling multiple sources by crawling from a set of predefined URLs, each requiring specific methods for data fetching and parsing. The class optimizes data retrieval and parsing through parallel processing.

    :param url: The URL from which to crawl events.
    :type url: str
    :param data_grabber: An instance of a data grabbing class with methods for fetching and parsing event data.
    :type data_grabber: Callable
    :param postgres_worker: An instance of a class responsible for writing data to a PostgreSQL database.
    :type postgres_worker: Callable

    :Example:

    .. code-block:: python

        berlinde_url = "https://www.berlin.de/polizei/service/versammlungsbehoerde/versammlungen-aufzuege"
        ecrawler = EventCrawler(berlinde_url, ProtestGrabber, ProtestPostgres)

        # To crawl data
        data = ecrawler.crawl(number_of_threads=8, save_to_database=True)
        print(f"Number of protests: {len(data)}")

    .. note:: This class provides a high-level interface for event data crawling, parsing, and optional database storage.

    .. warning:: Ensure that the `data_grabber` and `postgres_worker` classes are correctly implemented to avoid runtime errors.
    """

    def __init__(self, url, data_grabber, postgres_worker):
        self.url = url
        self.data_grabber = data_grabber()
        self.postgres_worker = postgres_worker(config())

    def get_event_list(self):
        return asyncio.run(self.data_grabber.get_protest_list(self.url))

    @property
    def parse_event_list(self):
        return self.data_grabber.parse_protest_list

    @property
    def write_to_database(self):
        return self.postgres_worker.write_to_database

    @staticmethod
    def _run_in_parallel(parser, data, number_of_threads, **kwargs):
        output_data = []

        def _parser(task_queue, **kwargs):
            while True:
                task = task_queue.get()
                output_data.append(parser(task, **kwargs))
                task_queue.task_done()

        queue = Queue()

        for _ in range(number_of_threads):
            worker = threading.Thread(target=_parser, args=(queue,), kwargs=kwargs)
            worker.daemon = True
            worker.start()

        for event in data:
            queue.put(event)

        queue.join()
        return output_data

    @staticmethod
    def _run_in_sequence(parser, data, **kwargs):
        for event in data:
            yield parser(event, **kwargs)

    def crawl(self, number_of_threads=1, save_to_database=True, **kwargs):
        event_list = self.get_event_list()
        concurrent_threads = number_of_threads
        if concurrent_threads > 1:
            crawled_data = self._run_in_parallel(
                self.parse_event_list, event_list, concurrent_threads, **kwargs
            )
        else:
            crawled_data = self._run_in_sequence(
                self.parse_event_list, event_list, **kwargs
            )

        if save_to_database:
            print("Writing/Updating data in database")
            write_response = self.write_to_database(crawled_data)
            if write_response:
                print("Writing/Updating data in database is done.")
            else:
                print("There seems to be a problem with your database.")

        return event_list


berlinde_url = (
    "https://www.berlin.de/polizei/service/versammlungsbehoerde/versammlungen-aufzuege"
)

if __name__ == "__main__":
    while True:
        ecrawler = EventCrawler(berlinde_url, ProtestGrabber, ProtestPostgres)
        print()
        print(datetime.now())
        try:
            print("Scraping data from berlin.de")
            lendata = len(
                ecrawler.crawl(
                    number_of_threads=1,
                    save_to_database=True,
                )
            )
            print("Number of protests:", lendata)
            print("Scraping data finished.")
            sleep(60 * 60)
        except Exception as e:
            print("An error occured when retrieving data from the internet.")
            print(e)
            sleep(10)
