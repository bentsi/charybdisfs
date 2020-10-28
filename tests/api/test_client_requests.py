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

import errno

import pytest

from core.faults import LatencyFault, ErrorFault, SysCall


pytestmark = pytest.mark.usefixtures("start_api_server")


def test_add_latency_fault(api_client):
    with api_client:
        latency_fault = LatencyFault(sys_call=SysCall.WRITE, probability=100, delay=1000)
        fault_id, response = api_client.add_fault(fault=latency_fault)
    assert response.ok, f"Request failed. Status: {response.status_code}\n Text: {response.text}"


def test_add_error_fault(api_client):
    with api_client:
        error_fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.EADV)
        fault_id, response = api_client.add_fault(fault=error_fault)

    assert response.ok and fault_id, f"Request failed. Status: {response.status_code}\n Text: {response.text}"


def test_remove_fault(api_client):
    with api_client:
        error_fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.EADV)
        fault_id, _ = api_client.add_fault(fault=error_fault)
        response = api_client.remove_fault(fault_id=fault_id)

    assert response.ok, f"Request failed. Status: {response.status_code}\n Text: {response.text}"


def test_get_active_faults(api_client):
    with api_client:
        error_fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.EADV)
        fault_id, _ = api_client.add_fault(fault=error_fault)
        response = api_client.get_active_faults()

    assert response.ok and response.text == f'{{"faults_ids": ["{fault_id}"]}}', \
        f"Request failed. Status: {response.status_code}\n Text: {response.text}"
