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

    @mock.patch("availability.config.CONF", new=None)
    @mock.patch("availability.config.os.environ.get")
    @mock.patch("availability.config.open", create=True)
    @mock.patch("availability.config.json.load")
    @mock.patch("availability.config.jsonschema.validate")
    def test_get_config(self, mock_validate, mock_load, mock_open, mock_get):
        mock_get.return_value = "foo_path"
        mock_load.return_value = {"foo": 42, "bar": "spam"}
        mock_open.return_value = "foo_stream"

        cfg = config.get_config()

        self.assertEqual({"foo": 42, "bar": "spam"}, cfg)
        mock_get.assert_called_once_with(
            "AVAILABILITY_CONF", "/etc/availability/config.json")
        mock_open.assert_called_once_with("foo_path")
        mock_load.assert_called_once_with("foo_stream")
        mock_validate.assert_called_once_with({"foo": 42, "bar": "spam"},
                                              config.CONF_SCHEMA)

    @mock.patch("availability.config.CONF", new=None)
    @mock.patch("availability.config.os.environ.get")
    @mock.patch("availability.config.open", create=True)
    @mock.patch("availability.config.json.load")
    @mock.patch("availability.config.jsonschema.validate")
    def test_get_config_open_error(
            self, mock_validate, mock_load, mock_open, mock_get):
        mock_open.side_effect = IOError
        cfg = config.get_config()
        self.assertEqual(config.DEFAULT_CONF, cfg)

    @mock.patch("availability.config.CONF", new=None)
    @mock.patch("availability.config.os.environ.get")
    @mock.patch("availability.config.open", create=True)
    @mock.patch("availability.config.json.load")
    @mock.patch("availability.config.jsonschema.validate")
    def test_get_config_validation_error(
            self, mock_validate, mock_load, mock_open, mock_get):
        validation_exc = jsonschema.exceptions.ValidationError
        mock_validate.side_effect = validation_exc(1)

        self.assertRaises(validation_exc, config.get_config)

    @mock.patch("availability.config.CONF", new=42)
    def test_get_config_cached(self):
        self.assertEqual(42, config.get_config())

    def test_validate_default_config(self):
        jsonschema.validate(config.DEFAULT_CONF, config.CONF_SCHEMA)
