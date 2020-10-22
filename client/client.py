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

from requests import Session, Request, Response


class CharybdisFsClient(Session):

    def send_request(self, host: str, method: str, json: str=None, timeout=10, resource: str=None, fault_id: str=None,
                     port: str=None, use_https:bool=False) -> Response:
        # Do we need authentication?
        # self.auth = ('user', 'pass')
        http = "http" if not use_https else "https"

        # Next 3 parameters may be None in the unit tests
        port = f':{port}' if port is not None else ''
        resource = f'/{resource}' if resource is not None else ''
        fault_id = f'/{fault_id}' if fault_id is not None else ''

        url = f"{http}://{host}{port}{resource}{fault_id}"

        req = Request(method=method, url=url, json=json)
        prepped_request = self.prepare_request(request=req)
        response = self.send(request=prepped_request, timeout=timeout)

        return response
