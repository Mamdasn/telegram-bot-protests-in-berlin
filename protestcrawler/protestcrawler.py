from urllib.parse import urlparse
from queue import Queue
import threading
import time
from ProtestLibs import ProtestGrabber, ProtestPostgres


class EventCrawler:
    def __init__(self, methods):
        self.url = None
        self._supported_methods = methods

    @property
    def _url_base(self):
        return urlparse(self.url).hostname

    def _is_supported(self):
        if self._url_base in self._supported_methods:
            return True
        else:
            return False

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

    def crawl(self, url, number_of_threads=1, save_to_database=True, **kwargs):
        self.url = url
        if not self._is_supported():
            raise ValueError(
                f"This url is not supported!\nPlease include the internet protocol,e.g. http https, "
                f"in url.\nSupported urls: {[k for k in self._supported_methods]}"
            )
            pass

        get_event_list = self._supported_methods[f"{self._url_base}"]["get_event_list"]
        parse_event_list = self._supported_methods[f"{self._url_base}"][
            "parse_event_list"
        ]

        event_list = get_event_list(self.url)
        concurrent_threads = number_of_threads
        crawled_data = self._run_in_parallel(
            parse_event_list, event_list, concurrent_threads, **kwargs
        )

        if save_to_database:
            print("Writing/Updating data in database")
            write_to_database = self._supported_methods[f"{self._url_base}"][
                "write_to_database"
            ]
            write_response = write_to_database(crawled_data)
            if write_response:
                print("Writing/Updating data in database is done.")
            else:
                print("There seems to be a problem with your database.")

        return crawled_data


# Define a method
method = {
    "www.berlin.de": {
        "get_event_list": ProtestGrabber.get_protest_list,
        "parse_event_list": ProtestGrabber.parse_protest_list,
        "write_to_database": ProtestPostgres.write_to_database,
    }
}
ecrawler = EventCrawler(method)
while True:
    print("Scraping data from berlin.de")
    url = "https://www.berlin.de/polizei/service/versammlungsbehoerde/versammlungen-aufzuege"
    data = ecrawler.crawl(
        url,
        number_of_threads=8,
        save_to_database=True,
    )
    print("Number of protests:", len(data))
    print("Scraping data finished.")
    time.sleep(21600)
