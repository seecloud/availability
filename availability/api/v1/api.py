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

import collections
import logging

import flask

from availability import config
from availability import storage


LOG = logging.getLogger("api")
LOG.setLevel(config.get_config().get("logging", {}).get("level", "INFO"))


def process_es_response(es_response, round_status_to=3):
    """Process ES availability search response.

    Transform ES response into API response format
    and calculate average of status values.

    :param es_response: Elasticsearch response dict
    :returns: tuple (list, float) - reformatted list
              and float average status
    :returns: None is something went wrong
    :rtype: tuple
    :rtype: None
    """

    try:
        buckets = es_response["aggregations"]["availability"]["buckets"]
    except KeyError as e:
        LOG.error("Unexpected Elasticsearch data: %s" % str(e))
        return None

    data = collections.deque()
    status_sum = 0

    try:
        for b in buckets:
            status = round(b["status"]["value"], round_status_to)
            status_sum += status
            data.append([b["key_as_string"], status])
    except (TypeError, KeyError) as e:
        LOG.error("Failed to process Elasticsearch buckets: %s" % str(e))
        return None

    data = list(data)
    avg = round((status_sum / len(data)), round_status_to)
    return (data, avg)

PERIODS = {
    "day": ("now-1d", "1h"),
    "week": ("now-1w", "1d"),
    "month": ("now-1M", "1d")
}


def make_region_query(period):
    if period not in PERIODS:
        return None

    gte, interval = PERIODS[period]

    return {
        "size": 0,
        "query": {
            "range": {
                "time": {
                    "lte": "now",
                    "gte": gte,
                    "format": "date_optional_time"
                }
            }
        },
        "aggs": {
            "availability": {
                "date_histogram": {
                    "field": "time",
                    "interval": interval,
                    "format": "yyyy-MM-dd'T'HH:mm",
                    "min_doc_count": 0
                },
                "aggs": {
                    "status": {"avg": {"field": "status"}}
                }
            }
        }
    }


def region_availability(region, period):
    body = make_region_query(period)
    if body:
        response = storage.es_search(region, body)
        if response:
            data = process_es_response(response)
            if data:
                availability, avg = data
            else:
                # NOTE(amaretskiy): Let's jsut reset this for now
                availability, avg = [], 0
            return {"availability": avg, "data": availability}

    return None


bp = flask.Blueprint("availability", __name__)


@bp.route("/<period>")
def get_availability(period):
    availability = {}
    for reg in config.get_config().get("regions"):
        region = reg["name"]
        data = region_availability(region, period)
        if not data:
            # TODO(maretskiy): Need better error handling here
            return flask.jsonify({"error": "Not found"}), 404
        availability[region] = data
    return flask.jsonify({"availability": availability,
                          "period": period})


@bp.route("/region/<region>/<period>")
def get_region_availability(region, period):
    data = region_availability(region, period)
    if not data:
        return flask.jsonify({"error": "Not found"}), 404
    availability = {"availability": {region: data},
                    "period": period}
    return flask.jsonify(availability)


def get_blueprints():
    return [["/availability", bp]]
