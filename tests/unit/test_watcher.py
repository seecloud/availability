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
import requests

from availability import storage
from availability import watcher
from tests.unit import test


class WatcherTestCase(test.TestCase):

    @mock.patch("availability.watcher.requests.get")
    @mock.patch("availability.watcher.LOG")
    def test_check_availability(self, mock_log, mock_get):
        mock_queue = mock.Mock()
        mock_get.side_effect = ValueError
        watcher.check_availability({"url": "http://foo/"}, mock_queue)
        mock_queue.put.assert_called_once_with({"url": "http://foo/",
                                                "status": 0})
        mock_get.reset_mock()
        mock_queue.put.reset_mock()
        mock_get.side_effect = None

        result = watcher.check_availability({"url": "http://foo/"},
                                            mock_queue)
        self.assertIsNone(result)
        mock_get.assert_called_once_with(
            "http://foo/", verify=False,
            timeout=(watcher.SERVICE_CONN_TIMEOUT,
                     watcher.SERVICE_READ_TIMEOUT))
        mock_queue.put.assert_called_once_with({"url": "http://foo/",
                                                "status": 1})

        mock_queue.reset_mock()
        mock_get.side_effect = requests.exceptions.RequestException
        result = watcher.check_availability({"url": "http://foo/"},
                                            mock_queue)
        self.assertIsNone(result)
        mock_queue.put.assert_called_once_with({"url": "http://foo/",
                                                "status": 0})

    @mock.patch("availability.watcher.storage")
    @mock.patch("availability.watcher.uuid")
    @mock.patch("availability.watcher.json.dumps")
    @mock.patch("availability.watcher.config.get_config")
    @mock.patch("availability.watcher.LOG")
    def test_save_availability(self, mock_log, mock_get_config, mock_dumps,
                               mock_uuid, mock_storage):
        backend = {"type": "elastic", "connection": "foo_connection"}
        mock_get_config.return_value = {"backend": backend}
        mock_queue = mock.Mock()
        queue_side_effect = [{"region": "foo"}, {"region": "bar"},
                             watcher.queue.Empty]
        mock_queue.get.side_effect = queue_side_effect

        backend = {"type": "elastic", "connection": "foo_connection"}
        mock_get_config.return_value = {"backend": backend}
        mock_dumps.side_effect = ["value-1", "value-2", "value-3", "value-4"]
        mock_es = mock.Mock()
        mock_storage.get_elasticsearch.return_value = mock_es
        mock_uuid.uuid1.side_effect = ["uuid-1", "uuid-2"]

        self.assertIsNone(watcher.save_availability(mock_queue))
        mock_es.bulk.assert_called_once_with(
            body="value-1\nvalue-2\nvalue-3\nvalue-4\n")
        mock_storage.get_elasticsearch.assert_called_once_with()
        self.assertEqual(
            [mock.call("ms_availability_foo"),
             mock.call("ms_availability_bar")],
            mock_storage.ensure_es_index_exists.mock_calls)
        self.assertEqual([mock.call(True, timeout=3)] * 3,
                         mock_queue.get.mock_calls)
        calls = [
            mock.call({"index": {"_type": "service_availability",
                                 "_id": "uuid-1",
                                 "_index": "ms_availability_foo"}}, indent=0),
            mock.call({"region": "foo"}, indent=0),
            mock.call({"index": {"_type": "service_availability",
                                 "_id": "uuid-2",
                                 "_index": "ms_availability_bar"}}, indent=0),
            mock.call({"region": "bar"}, indent=0)]
        self.assertEqual(calls, mock_dumps.mock_calls)

        mock_dumps.side_effect = ["value-1", "value-2", "value-3", "value-4"]
        mock_uuid.uuid1.side_effect = ["uuid-1", "uuid-2"]
        mock_queue.get.side_effect = queue_side_effect
        mock_es.bulk.side_effect = (
            watcher.es_exceptions.ElasticsearchException)
        self.assertIsNone(watcher.save_availability(mock_queue))

    @mock.patch("availability.watcher.dt")
    @mock.patch("availability.watcher.config.get_config")
    @mock.patch("availability.watcher.threading.Thread")
    @mock.patch("availability.watcher.results_queue")
    @mock.patch("availability.watcher.LOG")
    def test_watch_services(self, mock_log, mock_queue, mock_thread,
                            mock_get_config, mock_dt):
        mock_isoformat = mock.Mock()
        mock_isoformat.side_effect = ["time-1", "time-2"]
        mock_dt.datetime.now.return_value.isoformat = mock_isoformat
        regions = {"regions": [
            {"name": "a_reg",
             "services": [{"name": "a_svc", "url": "a_url"}]},
            {"name": "b_reg",
             "services": [{"name": "b_svc", "url": "b_url"}]}]}
        mock_get_config.return_value = regions
        watcher.watch_services()
        mock_get_config.assert_called_once_with()
        calls = [
            mock.call(args=({"url": "a_url", "region": "a_reg",
                             "name": "a_svc", "timestamp": "time-1"},
                            mock_queue),
                      target=watcher.check_availability),
            mock.call().start(),
            mock.call(args=({"url": "b_url", "region": "b_reg",
                             "name": "b_svc", "timestamp": "time-2"},
                            mock_queue),
                      target=watcher.check_availability),
            mock.call().start(),
            mock.call(args=(mock_queue,), target=watcher.save_availability),
            mock.call().start()]
        self.assertEqual(calls, mock_thread.mock_calls)

    @mock.patch("availability.watcher.schedule")
    @mock.patch("availability.watcher.storage.get_elasticsearch")
    @mock.patch("availability.watcher.watch_services")
    @mock.patch("availability.watcher.config.get_config")
    @mock.patch("availability.watcher.time")
    @mock.patch("availability.watcher.LOG")
    def test_main(self, mock_log, mock_time, mock_get_config,
                  mock_watch_services, mock_get_elastic, mock_schedule):
        class BreakInfinityCicle(Exception):
            pass

        run_effect = [None, None, None, BreakInfinityCicle]
        mock_schedule.run_pending.side_effect = run_effect

        mock_get_config.return_value = {}
        self.assertEqual(1, watcher.main())

        mock_get_config.return_value = {"regions": []}
        self.assertEqual(1, watcher.main())

        mock_get_config.return_value = {"regions": ["foo_region"]}
        # NOTE(amaretskiy):
        #   SERVICE_CONN_TIMEOUT + SERVICE_READ_TIMEOUT > 10
        self.assertEqual(1, watcher.main(10))

        backend = {"type": "unexpected", "connection": "foo_conn"}
        mock_get_config.return_value = {"regions": ["foo_region"],
                                        "backend": backend}
        self.assertEqual(1, watcher.main())

        backend = {"type": "elastic", "connection": "foo_conn"}
        mock_get_config.return_value = {"regions": ["foo_region"],
                                        "backend": backend}
        mock_get_elastic.side_effect = storage.StorageException
        self.assertEqual(1, watcher.main())
        mock_get_elastic.assert_called_once_with(
            check_availability=True)

        mock_get_elastic.reset_mock()
        mock_get_elastic.side_effect = None

        self.assertRaises(BreakInfinityCicle, watcher.main)
        self.assertEqual([mock.call(1)] * 4, mock_time.sleep.mock_calls)
        mock_schedule.every.assert_called_once_with(60)
        mock_get_elastic.assert_called_once_with(check_availability=True)

        mock_get_config.return_value = {"regions": ["foo_region"],
                                        "backend": backend, "period": 42}
        mock_schedule.reset_mock()
        mock_schedule.run_pending.side_effect = run_effect
        mock_time.reset_mock()
        self.assertRaises(BreakInfinityCicle, watcher.main)
        self.assertEqual([mock.call(1)] * 4, mock_time.sleep.mock_calls)
        mock_schedule.every.assert_called_once_with(42)
        mock_schedule.every.return_value.seconds.do.assert_called_once_with(
            mock_watch_services)
        self.assertEqual([mock.call()] * 4,
                         mock_schedule.run_pending.mock_calls)
