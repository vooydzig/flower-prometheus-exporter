==========================
flower-prometheus-exporter
==========================

flower-prometheus-exporter is a little exporter for Celery related metrics based on Flower API in 
order to get picked up by Prometheus. Main idea is to setup alerting based on flower monitoring. 
This was *hugely* inspired by celery-prometheus-exported. 

So far it provides access to the following metrics:

* `celery_tasks` exposes the number of tasks currently known to the queue
  grouped by `flower host`
* `celery_tasks_by_name` exposes the number of tasks currently known to the queue
  grouped by `name` and `flower host`.

How to use
==========
1. Git clone
2. Run in terminal: `$ python flower-prometheus-exporter`

  ```
  [2019-02-17 22:45:06,254: INFO/root] - Starting up on 0.0.0.0:8888
  [2019-02-17 22:45:06,254: INFO/root] - Setting metrics up
  [2019-02-17 22:45:06,254: INFO/monitor.http://127.0.0.1:5555] - Setting up monitor thread
  [2019-02-17 22:45:06,255: INFO/monitor.http://127.0.0.1:5555] - Running monitor thread for http://127.0.0.1:5555
  ```

Alternatively, you can use the bundle Dockerfile to generate a
Docker image.

By default, the HTTPD will listen at `0.0.0.0:8888`. If you want the HTTPD
to listen to another port, use the `--addr` option or the environment variable
`DEFAULT_ADDR`.

By default, this will expect the flower to be available through
`http://127.0.0.1:5555`, although you can change via environment variable
`FLOWER_HOSTS_LIST`. You can pass multiple flower hosts separated by space. 

For better logging use `--verbose` 

For example:
`python flower-prometheus-exporter --flower http://127.0.0.1:5000 http://127.0.0.1:6000 http://127.0.0.1:5555
`