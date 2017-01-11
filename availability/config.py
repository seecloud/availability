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

DEFAULT_CONF_PATH = "/etc/availability/config.yaml"

DEFAULT = {
    "backend": {
        "type": "elastic",
        "connection": [
            {"host": "127.0.0.1", "port": 9200},
        ],
    },
    "regions": [],
    "period": 60,
    "connection_timeout": 1,
    "read_timeout": 10,
}

SCHEMA = {
    "backend": {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "connection": {
                "type": "array",
                "items": {
                    # TODO(akscram): Here should be enum.
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                    },
                    "required": ["host"],
                    "additionalProperties": False,
                },
                "minItems": 1,
            },
        },
        "required": ["type", "connection"],
        "additionalProperties": False,
    },
    "regions": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "services": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "url": {"type": "string"}
                        },
                        "required": ["name", "url"],
                        "additionalProperties": False,
                    },
                    "minItems": 1,
                },
            },
            "additionalProperties": False,
        },
    },
    "period": {"type": "number", "minimum": 5},
    "connection_timeout": {"type": "number"},
    "read_timeout": {"type": "number"},
}
