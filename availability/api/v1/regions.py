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

import flask

from availability import storage


bp = flask.Blueprint("regions", __name__)


@bp.route("/", methods=["GET"])
def list_regions():
    """List regions names."""

    es = storage.get_elasticsearch()

    results = es.indices.get(index="ms_availability_*", feature="_mappings")
    return flask.jsonify([name[16:] for name in results])


def get_blueprints():
    return [["/regions", bp]]
