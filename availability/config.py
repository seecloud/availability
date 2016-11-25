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
import os

import jsonschema


CONF = None

DEFAULT_CONF = {
    "flask": {
        "HOST": "0.0.0.0",
        "PORT": 5000,
        "DEBUG": False
    },
    "backend": {
        "type": "elastic",
        "connection": {"host": "127.0.0.1", "port": 9200}
    },
    "regions": []
}

CONF_SCHEMA = {
    "type": "object",
    "$schema": "http://json-schema.org/draft-04/schema",
    "properties": {
        "flask": {
            "type": "object",
            "properties": {
                "PORT": {"type": "integer"},
                "HOST": {"type": "string"},
                "DEBUG": {"type": "boolean"}
            }
        },
        "backend": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "connection": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"}
                    },
                    "required": ["host"]
                }
            },
            "required": ["type", "connection"]
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
                            "required": ["name", "url"]
                        },
                        "minItems": 1
                    }
                }
            }
        },
        "period": {"type": "number", "minimum": 5},
        "connection_timeout": {"type": "number"},
        "read_timeout": {"type": "number"},
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string"}
            }
        }
    },
    "required": ["flask", "backend", "regions"]
}


def get_config():
    """Get cached configuration.

    :returns: application config
    :rtype: dict
    """
    global CONF
    if not CONF:
        path = os.environ.get("AVAILABILITY_CONF",
                              "/etc/oss/availability/config.json")
        try:
            cfg = json.load(open(path))
            logging.info("Config is '%s'" % path)
            jsonschema.validate(cfg, CONF_SCHEMA)
            CONF = cfg
        except (IOError, jsonschema.exceptions.ValidationError) as e:
            logging.warning("Failed to load config from '%s': %s" % (path, e))
            CONF = DEFAULT_CONF
    return CONF
