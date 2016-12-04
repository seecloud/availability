# Copyright 2016: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime as dt
import json
import logging
import sys
import threading
import time
import uuid

from elasticsearch import exceptions as es_exceptions
import queue
import requests
import schedule

from availability import config
from availability import storage


SERVICE_CONN_TIMEOUT = config.get_config().get("connection_timeout", 1)
SERVICE_READ_TIMEOUT = config.get_config().get("read_timeout", 10)

LOG = logging.getLogger("watcher")
LOG.setLevel(config.get_config().get("logging", {}).get("level", "INFO"))


def check_availability(data, results_queue):
    """Check if service is available and put result to Queue.

    :param data: dict that represents service query data
    :param results_queue: Queue for results
    :rtype: None
    """
    try:
        requests.get(data["url"], timeout=(SERVICE_CONN_TIMEOUT,
                                           SERVICE_READ_TIMEOUT))
        data["status"] = 1
    except Exception as e:
        data["status"] = 0
        LOG.warning("Something weng wrong while checking service %(name)s "
                    "by url %(url)s: %(exn)s" % {"name": data.get("name"),
                                                 "url": data.get("url"),
                                                 "exn": str(e)})
    results_queue.put(data)


def save_availability(results_queue):
    """Send availability data to storage backend.

    :param results_queue: queue.Queue which provides data to save
    :rtype: None
    """
    results = []
    timeout = 3

    while True:
        try:
            data = results_queue.get(True, timeout=timeout)
        except queue.Empty:
            break
        results.append(data)

    body = []
    indices = set()
    for data in results:
        index = "ms_availability_%(region)s" % data
        metadata = {"index": {"_index": index,
                              "_type": "service_availability",
                              "_id": str(uuid.uuid1())}}
        body.append(json.dumps(metadata, indent=0).replace("\n", ""))
        body.append("\n")
        body.append(json.dumps(data, indent=0).replace("\n", ""))
        body.append("\n")
        if index not in indices:
            storage.ensure_es_index_exists(index)
            indices.add(index)
    body = "".join(body)

    es = storage.get_elasticsearch()

    LOG.debug("Saving availability:\n%s" % body)
    try:
        es.bulk(body=body)
    except es_exceptions.ElasticsearchException as e:
        LOG.error("Failed to save availability to Elastic:\n"
                  "Body: %s\nError: %s" % (body, e))


results_queue = queue.Queue()


def watch_services():
    """Query services of all regions and save results."""
    for region in config.get_config().get("regions"):
        for service in region.get("services"):
            LOG.info("Checking service '%(name)s' availability on %(url)s"
                     % service)
            data = {
                "url": service["url"],
                "name": service["name"],
                "region": region["name"],
                "timestamp": dt.datetime.now().isoformat()
            }

            thr = threading.Thread(target=check_availability,
                                   args=(data, results_queue))
            thr.start()

    results_saver_thr = threading.Thread(target=save_availability,
                                         args=(results_queue,))
    results_saver_thr.start()


def main(period=None):
    """Constantly check services availability.

    This runs infinite availability check with given period.
    :param period: period in seconds
    """
    if not config.get_config().get("regions"):
        LOG.error("No regions configured. Quitting.")
        return 1

    period = period or config.get_config().get("period", 60)

    if SERVICE_CONN_TIMEOUT + SERVICE_READ_TIMEOUT > period:
        LOG.error("Period can not be lesser than timeout, "
                  "otherwise threads could crowd round.")
        return 1

    backend = config.get_config().get("backend")
    if backend["type"] != "elastic":
        LOG.error("Unexpected backend: %(type)s" % backend)
        return 1

    if not storage.get_elasticsearch(check_availability=True):
        LOG.error("Failed to set up Elasticsearch")
        return 1

    LOG.info("Start watching with period %s seconds" % period)
    schedule.every(period).seconds.do(watch_services)

    while True:
        time.sleep(1)
        schedule.run_pending()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        LOG.error("Got SIGINT. Quitting...")
