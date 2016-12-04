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

import logging

import flask

from availability import config
from availability import storage


LOG = logging.getLogger("api")
LOG.setLevel(config.get_config().get("logging", {}).get("level", "INFO"))


PERIODS = ["day", "week", "month"]


def get_period_interval(period):
    if period == "week":
        period = "now-7d/m"
        interval = "1h"
    elif period == "month":
        period = "now-30d/m"
        interval = "4h"
    elif period == "year":
        period = "now-365d/m"
        interval = "8h"
    else:
        # assuming day
        period = "now-1d/m"
        interval = "10m"
    return period, interval


def get_query(period, interval, aggs_name, aggs_term):
    query = {
        "size": 0,  # this is a count request
        "query": {
            "bool": {
                "filter": [{
                    "range": {
                        "timestamp": {
                            "gte": period
                        }
                    }
                }]
            }
        },
        "aggs": {
            aggs_name: {
                "terms": {"field": aggs_term},

                "aggs": {
                    "availability": {
                        "avg": {
                            "field": "status"
                        }
                    },
                    "data": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": interval,
                            "format": "yyyy-MM-dd'T'hh:mm",
                            "min_doc_count": 0,
                            "extended_bounds": {"min": period}
                        },
                        "aggs": {
                            "availability": {
                                "avg": {"field": "status"}
                            }
                        }
                    }
                }
            }
        }
    }
    return query


def process_results(buckets):
    result = {}

    for b in buckets:
        result[b["key"]] = {"availability": b["availability"]["value"]}
        result[b["key"]]["availability_data"] = [
            [d["key_as_string"], d["availability"]["value"]]
            for d in b["data"]["buckets"]
        ]

    return {"availability": result}


bp = flask.Blueprint("availability", __name__)


@bp.route('/availability', defaults={"period": "day"})
@bp.route("/availability/<period>")
def get_availability(period):
    if period not in PERIODS:
        flask.abort(404, "Wrong period %s" % period)

    start_at, interval = get_period_interval(period)
    query = get_query(start_at, interval, "regions", "region")

    es_result = storage.es_search("*", query)
    result = process_results(es_result["aggregations"]["regions"]["buckets"])
    result["period"] = period

    return flask.jsonify(result)


@bp.route('/region/<region>/availability', defaults={"period": "day"})
@bp.route("/region/<region>/availability/<period>")
def get_region_availability(region, period):
    if period not in PERIODS:
        flask.abort(404, "Wrong period %s" % period)

    start_at, interval = get_period_interval(period)
    query = get_query(start_at, interval, "services", "name")

    es_result = storage.es_search(region, query)
    result = process_results(es_result["aggregations"]["services"]["buckets"])
    result["period"] = period

    return flask.jsonify(result)


def get_blueprints():
    return [["", bp]]
