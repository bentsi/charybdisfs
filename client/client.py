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

import uuid

from requests import Session, Request, Response, ConnectionError


class CharybdisFsClient:
    rest_resource = 'faults'

    def __init__(self, host, port, timeout, use_https: bool = False):
        self._session = Session()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_https = use_https
        http = "http" if not self.use_https else "https"
        self.base_url = f"{http}://{self.host}{self.port}"
        self.connect()
        self.active_faults = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove_all_active_faults()
        self.close()

        if exc_val:
            raise

    def connect(self):
        response = self._session.get(self.base_url)
        if response.status_code != 200:
            raise ConnectionError

    def close(self):
        self._session.close()

    def send_request(self, resource, method, json: str=None, fault_id: str=None) -> Response:
        fault_id = f"/{fault_id}" if fault_id is None else ""
        url = f"{self.base_url}/{resource}{fault_id}"

        req = Request(method=method, url=url, json=json)
        prepped_request = self._session.prepare_request(request=req)
        response = self._session.send(request=prepped_request, timeout=self.timeout)
        return response

    def add_fault(self, fault):
        # TODO: convert fault object to json format
        data_json = fault
        fault_id = str(uuid.uuid4())

        response = self.send_request(resource=self.rest_resource, method ='POST', fault_id=fault_id, json=data_json)

        if response.status_code == 200:
            self.active_faults.append(fault_id)

        return response

    def remove_fault(self, fault_id: str):
        response = self.send_request(resource=self.rest_resource, method ='DELETE', fault_id=fault_id)

        if response.status_code == 200:
            self.active_faults.remove(fault_id)

        return response

    def get_active_fault(self):
        response = self.send_request(resource=self.rest_resource, method='POST')

        return response

    def remove_all_active_faults(self):
        for fault_id in self.active_faults:
            self.remove_fault(fault_id=fault_id)
