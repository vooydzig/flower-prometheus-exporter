import logging
import threading
import time

import prometheus_client
import requests

TASKS_QUEUE = prometheus_client.Gauge(
    'celery_tasks_by_queue',
    'Number of tasks per queue',
    ['flower', 'queue']
)


class MonitorThread(threading.Thread):

    def __init__(self, flower_host, *args, **kwargs):
        self.flower_host = flower_host
        self.log = logging.getLogger(f'monitor.{flower_host}')
        self.log.info('Setting up monitor thread')
        self.log.debug(f"Running monitoring thread for {self.flower_host} host.")
        self.setup_metrics()
        super().__init__(*args, **kwargs)

    def setup_metrics(self):
        logging.info("Setting metrics up")
        for metric in TASKS_QUEUE.collect():
            for sample in metric.samples:
                TASKS_QUEUE.labels(**sample[1]).set(0)

    def get_metrics(self):
        while True:
            self.log.debug(f"Getting workers data from {self.flower_host}")
            try:
                data = requests.get(self.endpoint)
            except requests.exceptions.ConnectionError as e:
                self.log.error(f'Error receiving data from {self.flower_host} - {e}')
                return
            if data.status_code != 200:
                self.log.error(f'Error receiving data from {self.flower_host}. '
                               f'Host responded with HTTP {data.status_code}')
                time.sleep(1)
                continue
            self.convert_data_to_prometheus(data.json())
            time.sleep(1)

    @property
    def endpoint(self):
        raise NotImplementedError

    def convert_data_to_prometheus(self, data):
        raise NotImplementedError

    def run(self):
        self.log.info(f'Running monitor thread for {self.flower_host}')
        self.get_metrics()


class QueueMonitorThread(MonitorThread):
    @property
    def endpoint(self):
        return self.flower_host + '/api/queues/length'

    def convert_data_to_prometheus(self, data):
        for q_info in data.get('active_queues', []):
            TASKS_QUEUE.labels(flower=self.flower_host, queue=q_info['name']).set(q_info['messages'])
