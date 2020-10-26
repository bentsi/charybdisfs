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

import logging
from typing import Tuple

from requests import Session, Request, Response, ConnectionError

LOGGER = logging.getLogger(__name__)


class CharybdisFsClient:
    rest_resource = 'faults'

    def __init__(self, host: str, port: int, timeout: int = 10, use_https: bool = False):
        self._session = Session()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_https = use_https
        http = "http" if not self.use_https else "https"
        self.base_url = f"{http}://{self.host}:{str(self.port)}"
        self.active_faults = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove_all_active_faults()
        self.close()

        if exc_val:
            raise

    def close(self):
        self._session.close()

    def send_request(self, resource, method, json: str = None, fault_id: str = None) -> Response:
        fault_id = f"/{fault_id}" if fault_id is not None else ""
        url = f"{self.base_url}/{resource}{fault_id}"

        LOGGER.debug("Send request to %s with json content:\n %s", url, json)
        req = Request(method=method, url=url, json=json)
        prepped_request = self._session.prepare_request(request=req)
        response = self._session.send(request=prepped_request, timeout=self.timeout)
        LOGGER.debug("Response status: %s; reason: %s", response.status_code, response.reason)
        return response

    def get_param_from_response(self, response: Response, param: str) -> str:
        json_content = response.json()
        param_value = json_content[param]
        LOGGER.debug("Param %s value from request is: %s", param, param_value)
        return param_value

    def add_fault(self, fault) -> Tuple[str, Response]:
        data_json = fault._serialize()

        response = self.send_request(resource=self.rest_resource, method='POST', json=data_json)

        fault_id = ''
        if response.status_code == 200:
            fault_id = self.get_param_from_response(response, 'fault_id')
            if fault_id:
                self.active_faults.append(fault_id)

        return fault_id, response

    def remove_fault(self, fault_id: str) -> Response:
        response = self.send_request(resource=self.rest_resource, method='DELETE', fault_id=fault_id)

        if response.status_code == 200:
            self.active_faults.remove(fault_id)

        return response

    def get_active_fault(self) -> Response:
        response = self.send_request(resource=self.rest_resource, method='GET')

        return response

    def remove_all_active_faults(self):
        for fault_id in self.active_faults:
            self.remove_fault(fault_id=fault_id)
