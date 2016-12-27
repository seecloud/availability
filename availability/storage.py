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

import json
import logging

import elasticsearch
from oss_lib import config

CONF = config.CONF
LOG = logging.getLogger(__name__)

NUMBER_OF_SHARDS = 2


def get_elasticsearch(check_availability=False):
    """Return Elasticsearch instance.

    :param check_availability: check if nodes are available
    :returns: Elasticsearch or None on failure
    :rtype: elasticsearch.Elasticsearch
    """
    nodes = CONF["backend"]["connection"]
    try:
        es = elasticsearch.Elasticsearch(nodes)
        if check_availability:
                es.info()
    except Exception as e:
        LOG.warning(
            "Failed to query Elasticsearch nodes %s: %s"
            % (nodes, str(e)))
        raise
    return es


def ensure_es_index_exists(index):
    """Create index if missed and return Elasticsearch instance.

    :param index: index name
    :returns: Elasticsearch or None on failure
    :rtype: elasticsearch.Elasticsearch
    """
    es = get_elasticsearch()
    try:
        if not es.indices.exists(index):
            mapping = {
                "settings": {
                    "number_of_shards": NUMBER_OF_SHARDS
                },
                "mappings": {
                    "service_availability": {
                        "_all": {"enabled": False},
                        "properties": {
                            "name": {"type": "keyword"},
                            "region": {"type": "keyword"},
                            "url": {"type": "text"},
                            "timestamp": {"type": "date"},
                            "status": {"type": "integer"}
                        }
                    }
                }
            }
            mapping = json.dumps(mapping)
            LOG.info("Creating Elasticsearch index: %s" % index)
            es.indices.create(index=index, body=mapping)
    except elasticsearch.exceptions.ElasticsearchException as e:
        LOG.warning(
            "Something went wrong with Elasticsearch: %s" % str(e))
        raise
    return es


def es_search(region, body):
    """Search availability by region.

    :param region: str region name
    :param body: dict ES query
    :returns: dict search results
    """
    es = get_elasticsearch()
    try:
        index = "ms_availability_%s" % region
        return es.search(index=index, doc_type="service_availability",
                         body=body)
    except elasticsearch.exceptions.ElasticsearchException as e:
        LOG.error("Search query has failed:\nIndex: %s\nBody: %s\nError: %s"
                  % (index, body, str(e)))
        raise
