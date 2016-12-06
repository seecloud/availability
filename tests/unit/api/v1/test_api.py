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

import mock

from tests.unit import test


class ApiTestCase(test.TestCase):

    @mock.patch("availability.api.v1.api.storage")
    @mock.patch("availability.api.v1.api.get_query")
    @mock.patch("availability.api.v1.api.process_results")
    def test_get_availability(self, mock_process_results, mock_get_query,
                              mock_storage):
        mock_get_query.return_value = "foo_query"
        mock_process_results.return_value = {"availability": "foo_data"}
        es_res = {"aggregations": {"regions": {"buckets": "foo_buckets"}}}
        mock_storage.es_search.return_value = es_res
        for period, start_et, interval in (("day", "now-1d/m", "10m"),
                                           ("week", "now-7d/m", "1h"),
                                           ("month", "now-30d/m", "4h"),
                                           ("year", "now-365d/m", "8h")):
            code, resp = self.get("/api/v1/availability/%s" % period)
            self.assertEqual(200, code)
            self.assertEqual({"availability": "foo_data", "period": period},
                             resp)
            mock_get_query.assert_called_once_with(
                start_et, interval, "regions", "region")
            mock_get_query.reset_mock()
            mock_storage.es_search.assert_called_once_with("*", "foo_query")
            mock_storage.es_search.reset_mock()
            mock_process_results.assert_called_once_with("foo_buckets")
            mock_process_results.reset_mock()

        code, resp = self.get("/api/v1/availability/otherday")
        self.assertEqual(404, code)

    @mock.patch("availability.api.v1.api.storage")
    @mock.patch("availability.api.v1.api.get_query")
    @mock.patch("availability.api.v1.api.process_results")
    def test_get_region_availability(self, mock_process_results,
                                     mock_get_query, mock_storage):
        mock_get_query.return_value = "foo_query"
        mock_process_results.return_value = {"availability": "foo_data"}
        es_res = {"aggregations": {"services": {"buckets": "foo_buckets"}}}
        mock_storage.es_search.return_value = es_res
        for period, start_et, interval in (("day", "now-1d/m", "10m"),
                                           ("week", "now-7d/m", "1h"),
                                           ("month", "now-30d/m", "4h"),
                                           ("year", "now-365d/m", "8h")):
            code, resp = self.get("/api/v1/region/foo_region/availability/%s"
                                  % period)
            self.assertEqual(200, code)
            self.assertEqual({"availability": "foo_data", "period": period},
                             resp)
            mock_get_query.assert_called_once_with(
                start_et, interval, "services", "name")
            mock_get_query.reset_mock()
            mock_storage.es_search.assert_called_once_with("foo_region",
                                                           "foo_query")
            mock_storage.es_search.reset_mock()
            mock_process_results.assert_called_once_with("foo_buckets")
            mock_process_results.reset_mock()
