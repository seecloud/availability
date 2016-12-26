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

from availability import main
from tests.unit import test


class MainTestCase(test.TestCase):

    def test_not_found(self):
        code, resp = self.get("/unexisting/path/to/somewhere/else")
        self.assertEqual(404, code)
        self.assertEqual({"error": "Not Found"}, resp)

    @mock.patch("availability.main.argparse.ArgumentParser")
    @mock.patch("availability.main.app")
    def test_main_default(self, mock_app, mock_parser):
        mock_parser.return_value.parse_args.return_value.configure_mock(**{
            "host": "0.0.0.0",
            "port": 5000,
        })
        main.main()
        mock_app.run.assert_called_once_with(host="0.0.0.0", port=5000)

    @mock.patch("availability.main.argparse.ArgumentParser")
    @mock.patch("availability.main.app")
    def test_main_custom(self, mock_app, mock_parser):
        mock_parser.return_value.parse_args.return_value.configure_mock(**{
            "host": "foo_host",
            "port": 42,
        })
        main.main()
        mock_app.run.assert_called_once_with(host="foo_host", port=42)

    def test_api_map(self):
        code, resp = self.get("/")
        self.assertEqual(200, code)
        self.assertEqual(3, len(resp))
        self.assertIn({"endpoint": u"availability.get_availability",
                       "methods": ["GET", "HEAD", "OPTIONS"],
                       "uri": "/api/v1/availability/<period>"}, resp)
