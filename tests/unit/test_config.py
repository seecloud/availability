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

from availability import config
from tests.unit import test


class ConfigTestCase(test.TestCase):

    @mock.patch("availability.config.json")
    @mock.patch("availability.config.os.environ")
    @mock.patch("availability.config.jsonschema.validate")
    @mock.patch("availability.config.open", create=True)
    def test_get_config(self, mock_open, mock_validate, mock_environ,
                        mock_json):
        def reset_mocks():
            for m in (mock_open, mock_validate, mock_environ, mock_json):
                m.reset_mock()

        config.CONF = None
        mock_json.load.return_value = {"foo": 42, "bar": "spam"}
        mock_environ.get.return_value = "foo_path"
        mock_open.return_value = "foo_stream"

        cfg = config.get_config()
        self.assertEqual({"foo": 42, "bar": "spam"}, cfg)
        mock_environ.get.assert_called_once_with(
            "AVAILABILITY_CONF", "/etc/availability/config.json")
        mock_open.assert_called_once_with("foo_path")
        mock_json.load.assert_called_once_with("foo_stream")
        mock_validate.assert_called_once_with({"foo": 42, "bar": "spam"},
                                              config.CONF_SCHEMA)

        reset_mocks()
        config.CONF = None
        mock_open.side_effect = IOError
        cfg = config.get_config()
        self.assertEqual(config.DEFAULT_CONF, cfg)

    def test_get_config_cached(self):
        config.CONF = 42
        self.assertEqual(42, config.get_config())
