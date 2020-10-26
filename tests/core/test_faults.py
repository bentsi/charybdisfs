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

from unittest.mock import patch

import pytest
import pyfuse3

from core.faults import LatencyFault, ErrorFault, SysCall, Status, create_fault_from_json


def test_latency_fault_to_json():
    assert LatencyFault(sys_call=SysCall.ALL, probability=50).to_json() == \
           '{"fault_type": "LatencyFault", "sys_call": "*", "probability": 50, "status": "new", "delay": 0}'
    assert LatencyFault(sys_call=SysCall.WRITE, probability=75, delay=1000).to_json() == \
           '{"fault_type": "LatencyFault", "sys_call": "write", "probability": 75, "status": "new", "delay": 1000}'


def test_latency_fault_from_json():
    fault = create_fault_from_json(
        '{"fault_type": "LatencyFault", "sys_call": "write", "probability": 75, "status": "applied", "delay": 1000}')
    assert isinstance(fault, LatencyFault)
    assert fault.sys_call == SysCall.WRITE
    assert fault.probability == 75
    assert fault.status == Status.APPLIED
    assert fault.delay == 1000


def test_latency_fault_from_dict_fail():
    assert LatencyFault.from_dict({}) is None


def test_latency_fault_apply():
    fault = LatencyFault(sys_call=SysCall.WRITE, probability=50, delay=666)
    with patch("time.sleep") as mock:
        fault.apply()
    mock.called_once_with(666)
    assert fault.status == Status.APPLIED


def test_latency_fault_to_json_and_back():
    fault = LatencyFault(sys_call=SysCall.WRITE, probability=50, delay=666)
    assert fault == create_fault_from_json(fault.to_json())


def test_error_fault_to_json():
    assert ErrorFault(sys_call=SysCall.ALL, probability=50, error_no=666).to_json() == \
           '{"fault_type": "ErrorFault", "sys_call": "*", "probability": 50, "status": "new", "error_no": 666}'


def test_error_fault_from_json():
    fault = create_fault_from_json(
        '{"fault_type": "ErrorFault", "sys_call": "write", "probability": 75, "status": "applied", "error_no": 13}')
    assert isinstance(fault, ErrorFault)
    assert fault.sys_call == SysCall.WRITE
    assert fault.probability == 75
    assert fault.status == Status.APPLIED
    assert fault.error_no == 13


def test_error_fault_from_dict_fail():
    assert ErrorFault.from_dict({}) is None


def test_error_fault_apply():
    fault = ErrorFault(sys_call=SysCall.ALL, probability=100, error_no=8)
    with pytest.raises(pyfuse3.FUSEError) as exc:
        fault.apply()
    assert fault.status == Status.APPLIED
    assert exc.value.errno == 8


def test_unknown_fault_from_json():
    fault = create_fault_from_json(
        '{"fault_type": "UnknownFault", "sys_call": "write", "probability": 75, "status": "applied", "error_no": 13}')
    assert fault is None


def test_error_fault_to_json_and_back():
    fault = ErrorFault(sys_call=SysCall.ALL, probability=100, error_no=8)
    assert fault == create_fault_from_json(fault.to_json())
