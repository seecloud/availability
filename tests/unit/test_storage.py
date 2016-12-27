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

import elasticsearch
import mock

from availability import storage
from tests.unit import test


class EnsureIndexTestCase(test.TestCase):
    @mock.patch("availability.storage.json.dumps")
    @mock.patch("availability.storage.LOG")
    @mock.patch("availability.storage.get_elasticsearch")
    def test_ensure_es_index_exists(
            self, mock_get_elastic, mock_log, mock_dumps):
        self.assertRaises(TypeError, storage.ensure_es_index_exists)

        mock_es = mock.Mock()
        mock_get_elastic.return_value = mock_es
        mock_es.indices.exists.side_effect = (
            storage.elasticsearch.exceptions.ElasticsearchException)
        self.assertRaises(elasticsearch.exceptions.ElasticsearchException,
                          storage.ensure_es_index_exists, "foo_index")

        mock_es.indices.exists.side_effect = None
        mock_es.indices.exists.return_value = False
        mock_dumps.return_value = "foo_dumped_str"
        self.assertEqual(
            mock_es,
            storage.ensure_es_index_exists("foo_index"))
        mapping = {
            "mappings": {
                "service_availability": {
                    "_all": {"enabled": False},
                    "properties": {
                        "url": {"type": "text"},
                        "status": {"type": "integer"},
                        "region": {"type": "keyword"},
                        "name": {"type": "keyword"},
                        "timestamp": {"type": "date"}}}},
            "settings": {"number_of_shards": storage.NUMBER_OF_SHARDS}}
        mock_dumps.assert_called_once_with(mapping)
        mock_es.indices.create.assert_called_once_with(
            body="foo_dumped_str", index="foo_index")


class GetElasticTestCase(test.TestCase):
    def setUp(self):
        super(GetElasticTestCase, self).setUp()
        self.mock_config({
            "backend": {
                "type": "elastic",
                "connection": [{"host": "node0"}],
            },
        })

    @mock.patch("availability.storage.elasticsearch.Elasticsearch")
    @mock.patch("availability.storage.LOG")
    def test_get_elasticsearch(self, mock_log, mock_elastic):
        result = storage.get_elasticsearch()

        self.assertFalse(mock_elastic.return_value.info.called)
        self.assertEqual(result, mock_elastic.return_value)
        mock_elastic.assert_called_once_with([{"host": "node0"}])

    @mock.patch("availability.storage.elasticsearch.Elasticsearch")
    @mock.patch("availability.storage.LOG")
    def test_get_elasticsearch_check(self, mock_log, mock_elastic):
        result = storage.get_elasticsearch(check_availability=True)

        self.assertTrue(mock_elastic.return_value.info.called)
        self.assertEqual(result, mock_elastic.return_value)
