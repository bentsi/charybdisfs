# Copyright 2020 ScyllaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import uuid
import logging
from typing import Optional

import cherrypy

from core.faults import create_fault_from_json
from core.configuration import Configuration


DEFAULT_PORT = 8080

LOGGER = logging.getLogger(__name__)


class CharybdisFsApiServer:
    @staticmethod
    def generate_new_uuid() -> str:
        return str(uuid.uuid4())

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def faults(self, fault_id: Optional[str] = None):  # noqa: C901  # ignore "is too complex" message
        method = cherrypy.request.method

        sys.audit("charybdisfs.api", method, fault_id, cherrypy.request)

        if method == "GET":
            if fault_id is None:
                return {"faults_ids": Configuration.get_all_faults_ids()}
            if fault := Configuration.get_fault_by_uuid(uuid=fault_id):
                return {"fault_id": fault_id, "fault": fault.to_json()}
            raise cherrypy.NotFound()

        elif method in ("POST", "CREATE", "PUT",):
            if fault_id:
                raise cherrypy.HTTPError(message="Replacing of a fault is not supported")
            if (fault := create_fault_from_json(json_data=cherrypy.request.json)) is None:
                raise cherrypy.HTTPError(message="Unable to create a fault from provided JSON data")
            try:
                fault_id = self.generate_new_uuid()
                Configuration.add_fault(uuid=fault_id, fault=fault)
            except ValueError as exc:
                raise cherrypy.HTTPError(message=f"Unable to add a fault {fault} with {fault_id=}: {exc}") from None
            return {"fault_id": fault_id}

        elif method == "DELETE":
            if Configuration.remove_fault(uuid=fault_id):
                return {"fault_id": fault_id}
            raise cherrypy.NotFound()


def start_charybdisfs_api_server(port: int = DEFAULT_PORT) -> None:
    conf = {
        "global": {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": port,
            "server.thread_pool": 1,
            "engine.autoreload.on": False,
        },
    }
    cherrypy.quickstart(root=CharybdisFsApiServer(), config=conf)


def stop_charydisfs_api_server() -> None:
    cherrypy.engine.exit()
