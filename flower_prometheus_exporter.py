import argparse
import logging
import os
import signal
import sys
import threading
import time

import prometheus_client
import requests

DEFAULT_ADDR = os.environ.get('DEFAULT_ADDR', '0.0.0.0:8888')
FLOWER_HOSTS_LIST = os.environ.get('FLOWER_HOSTS_LIST', 'http://127.0.0.1:5555').split()

LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(name)s] - %(message)s'

TASKS = prometheus_client.Gauge(
    'celery_tasks',
    'Number of tasks per flower instance',
    ['flower', 'worker']
)
TASKS_NAME = prometheus_client.Gauge(
    'celery_tasks_by_name',
    'Number of tasks per name',
    ['flower', 'worker', 'name']
)


class MonitorThread(threading.Thread):
    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f'monitor.{flower_host}')
        self.log.info('Setting up monitor thread')
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        super(MonitorThread, self).__init__(*args, **kwargs)

    @property
    def workers_endpoint(self):
        return self.flower_host + '/api/workers'

    @property
    def tasks_endpoint(self):
        return self.flower_host + '/api/tasks'

    def get_workers_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                data = requests.get(self.workers_endpoint)
            except requests.exceptions.ConnectionError as e:
                self.log.error(f'Error receiving data from {self.flower_host} - {e}')
                return
            if data.status_code != 200:
                self.log.error(f'Error receiving data from {self.flower_host}. '
                               f'Host responded with HTTP {data.status_code}')
                time.sleep(1)
                continue

            data = data.json()
            for worker, info in data.items():
                self.parse_worker(worker, info)
            time.sleep(1)

    def parse_worker(self, worker, info):
        self.log.debug(f'Parsing worker {worker}')
        tasks = info['stats']['total']
        total_tasks = sum(tasks.values())

        TASKS.labels(flower=self.flower_host, worker=worker).set(total_tasks)
        for task, cnt in tasks.items():
            TASKS_NAME.labels(flower=self.flower_host, worker=worker, name=task).set(cnt)

    def run(self):
        self.log.info(f'Running monitor thread for {self.flower_host}')
        self.get_workers_metrics()


def main():
    opts = parse_arguments()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logging.info(f"Starting up on {opts.addr}")
    setup_metrics()
    threads = setup_monitoring_threads(opts)
    start_httpd(opts.addr)
    for t in threads:
        t.join()


def setup_monitoring_threads(opts):
    threads = []
    logging.debug(f"Running {len(opts.flower_addr)} monitoring threads.")
    for flower_addr in opts.flower_addr:
        t = MonitorThread(flower_addr)
        t.daemon = True
        t.start()
        threads.append(t)
    return threads


def start_httpd(addr):
    host, port = addr.split(':')
    prometheus_client.start_http_server(int(port), host)


def setup_metrics():
    logging.info("Setting metrics up")
    for metric in TASKS.collect():
        for sample in metric.samples:
            TASKS.labels(**sample[1]).set(0)
    for metric in TASKS_NAME.collect():
        for sample in metric.samples:
            TASKS_NAME.labels(**sample[1]).set(0)


def shutdown(signum, frame):  # pragma: no cover
    logging.info("Shutting down")
    sys.exit(0)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--flower', dest='flower_addr', default=FLOWER_HOSTS_LIST, nargs='+',
        help="List of urls to the Flower monitor. Defaults to {}".format(FLOWER_HOSTS_LIST))
    parser.add_argument(
        '--addr', dest='addr', default=DEFAULT_ADDR,
        help="Address the HTTPD should listen on. Defaults to {}".format(
            DEFAULT_ADDR))
    parser.add_argument(
        '--verbose', action='store_true', default=False,
        help="Enable verbose logging")
    opts = parser.parse_args()
    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    return opts


if __name__ == '__main__':  # pragma: no cover
    main()
