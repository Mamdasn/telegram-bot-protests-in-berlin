import asyncio
import logging
import random
import threading
from datetime import datetime
from queue import Queue
from time import sleep

from ProtestLibs import ProtestGrabber, ProtestPostgres

from credentials import config as envconfig


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
    """

    def __init__(self, url, data_grabber, postgres_worker):
        self.url = url
        self.data_grabber = data_grabber
        self.postgres_worker = postgres_worker

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
            logger.info("Writing/Updating data in database")
            write_response = self.write_to_database(crawled_data)
            if write_response:
                logger.info("Writing/Updating data in database is done.")
            else:
                logger.warn("There seems to be a problem with your database.")

        return event_list


CRAWLER_UA_UNIQ_ID = random.randint(10**11, 10**12 - 1)

berlinde_url = (
    "https://www.berlin.de/polizei/service/versammlungsbehoerde/versammlungen-aufzuege"
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Crawler app has started.")
    ecrawler = EventCrawler(berlinde_url, ProtestGrabber(CRAWLER_UA_UNIQ_ID), ProtestPostgres(envconfig.POSTGRES))
    while True:
        try:
            logger.info("Scraping data from berlin.de")
            lendata = len(
                ecrawler.crawl(
                    number_of_threads=1,
                    save_to_database=True,
                )
            )
            logger.info(f"Number of protests: {lendata}")
            logger.info("Scraping data finished.")
            sleep(envconfig.DB_UPDATE_PERIOD)
        except Exception as e:
            logger.error(f"An error occured when retrieving data from the internet. Error: {e}")
            sleep(10)
