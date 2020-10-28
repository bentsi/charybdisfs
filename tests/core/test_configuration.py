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

from core.faults import ErrorFault, SysCall
from core.rest_api import CharybdisFsApiServer


new_uuid = CharybdisFsApiServer.generate_new_uuid


def test_add_fault(configuration):
    fault1_uuid = new_uuid()
    fault2_uuid = new_uuid()
    fault3_uuid = new_uuid()
    fault4_uuid = new_uuid()
    fault1 = ErrorFault(sys_call=SysCall.WRITE, probability=41, error_no=errno.ENOSPC)
    fault2 = ErrorFault(sys_call=SysCall.READ, probability=60, error_no=errno.ENOSPC)
    fault3 = ErrorFault(sys_call=SysCall.ALL, probability=50, error_no=errno.ENOSPC)
    fault4 = ErrorFault(sys_call=SysCall.WRITE, probability=59, error_no=errno.ENOSPC)
    fault5 = ErrorFault(sys_call=SysCall.WRITE, probability=1, error_no=errno.ENOSPC)

    # One fault.
    configuration.add_fault(uuid=fault1_uuid, fault=fault1)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, }

    # Try add the same fault again.
    with pytest.raises(ValueError):
        configuration.add_fault(uuid=fault1_uuid, fault=fault1)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, }

    # Try to reuse uuid with another fault.
    with pytest.raises(ValueError):
        configuration.add_fault(uuid=fault1_uuid, fault=fault2)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, }

    # Another fault with different type.
    configuration.add_fault(uuid=fault2_uuid, fault=fault2)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, fault2_uuid: fault2, }

    # SysCall.ALL which exceeds probability of some SysCall.
    with pytest.raises(ValueError):
        configuration.add_fault(uuid=fault3_uuid, fault=fault3)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, fault2_uuid: fault2, }

    # Exactly 100% probability.
    configuration.add_fault(uuid=fault3_uuid, fault=fault4)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, fault2_uuid: fault2, fault3_uuid: fault4, }

    # Exceed SysCall.WRITE probability.
    with pytest.raises(ValueError):
        configuration.add_fault(uuid=fault4_uuid, fault=fault5)
    assert configuration.syscalls_conf == {fault1_uuid: fault1, fault2_uuid: fault2, fault3_uuid: fault4, }


def test_remove_fault(configuration):
    fault_uuid = new_uuid()
    fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.ENOSPC)
    configuration.add_fault(uuid=fault_uuid, fault=fault)
    assert configuration.remove_fault(uuid=fault_uuid) == fault
    assert configuration.syscalls_conf == {}
    assert configuration.remove_fault(uuid=fault_uuid) is None


def test_get_fault_by_uuid(configuration):
    fault_uuid = new_uuid()
    another_fault_uuid = new_uuid()
    fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.ENOSPC)
    configuration.add_fault(uuid=fault_uuid, fault=fault)
    assert configuration.get_fault_by_uuid(uuid=fault_uuid) == fault
    assert configuration.get_fault_by_uuid(uuid=another_fault_uuid) is None
    assert configuration.syscalls_conf == {fault_uuid: fault}


def test_get_faults_by_sys_call(configuration):
    fault1_uuid = new_uuid()
    fault2_uuid = new_uuid()
    fault3_uuid = new_uuid()
    fault1 = ErrorFault(sys_call=SysCall.WRITE, probability=10, error_no=errno.ENOSPC)
    fault2 = ErrorFault(sys_call=SysCall.READ, probability=10, error_no=errno.ENOSPC)
    fault3 = ErrorFault(sys_call=SysCall.ALL, probability=10, error_no=errno.ENOSPC)
    configuration.add_fault(uuid=fault1_uuid, fault=fault1)
    configuration.add_fault(uuid=fault2_uuid, fault=fault2)
    configuration.add_fault(uuid=fault3_uuid, fault=fault3)
    assert configuration.get_faults_by_sys_call(sys_call=SysCall.WRITE) == [fault1, fault3]
    assert configuration.get_faults_by_sys_call(sys_call=SysCall.READ) == [fault2, fault3]
    assert configuration.get_faults_by_sys_call(sys_call=SysCall.ALL) == [fault3]
    assert configuration.get_all_faults() == [fault1, fault2, fault3]
    assert configuration.get_all_faults_ids() == [fault1_uuid, fault2_uuid, fault3_uuid]
