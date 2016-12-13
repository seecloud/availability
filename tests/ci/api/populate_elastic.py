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
import os
import random
import sys
import uuid

from availability import storage


"""Populate Elasticsearch by availability data."""


def compose_bulk_requests(regions, ts_interval, ts_in_bunch, bunches):
    def random_status(success_probability=0.7):
        return int(random.random() < success_probability)

    minus_seconds = 0
    for bunch in range(bunches):
        body = []

        for i in range(ts_in_bunch):
            minus_seconds += ts_interval
            delta = dt.timedelta(0, minus_seconds)
            ts = (dt.datetime.now() - delta).isoformat()

            for region, services in regions.items():
                for service in services:
                    meta = {"index": {"_index": "ms_availability_%s" % region,
                                      "_type": "service_availability",
                                      "_id": str(uuid.uuid1())}}
                    data = {"url": service["url"],
                            "name": service["name"],
                            "region": region,
                            "timestamp": ts,
                            "status": random_status()}
                    body.extend(
                        [json.dumps(meta, indent=0).replace("\n", ""), "\n",
                         json.dumps(data, indent=0).replace("\n", ""), "\n"])
        yield "".join(body)


def populate_elastic(**kwargs):
    started_at = dt.datetime.now()
    conf = json.load(open(os.environ.get("AVAILABILITY_CONF")))
    regions = {r["name"]: r["services"] for r in conf["regions"]}
    elastic = storage.get_elasticsearch(check_availability=True)

    # Create indices
    for region in regions:
        storage.ensure_es_index_exists("ms_availability_%s" % region)

    # Load availability data
    for request_body in compose_bulk_requests(regions, **kwargs):
        response = elastic.bulk(body=request_body)
        sys.stdout.write("F" if response["errors"] else ".")
    duration = dt.datetime.now() - started_at
    sys.stdout.write("\nDone in %i seconds\n" % duration.seconds)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tsi, bsize, bnum = map(int, sys.argv[1:])
    else:
        tsi, bsize, bnum = 30, 5000, 5  # Defaults
    days = (tsi * bsize * bnum) / 86400  # 1 day is 86400 seconds
    mesg = ("%i days (%i x %i-seconds intervals)" % (days, bnum * bsize, tsi))
    sys.stdout.write("Start populating availability data for %s ...\n" % mesg)

    populate_elastic(ts_interval=tsi, ts_in_bunch=bsize, bunches=bnum)
