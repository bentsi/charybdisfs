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

from client.client import CharybdisFsClient


def add_fault(node_ip: str, fault, timeout: int = 10):
    # TODO: convert fault object to json format
    data_json = fault
    with CharybdisFsClient() as fs_client:
        return fs_client.send_request(host=node_ip, method='POST', resource='faults', fault_id=str(uuid.uuid4()),
                                      json=data_json, timeout=timeout)


def remove_fault(node_ip: str, timeout: int = 10):
    with CharybdisFsClient() as fs_client:
        return fs_client.send_request(host=node_ip, method='POST', resource='', fault_id=str(uuid.uuid4()),
                                      timeout=timeout)


def get_active_fault(node_ip: str, timeout: int = 10):
    with CharybdisFsClient() as fs_client:
        return fs_client.send_request(host=node_ip, method='POST', resource='', timeout=timeout)
