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
import threading
from typing import NewType, Dict, Optional, List

from core.faults import BaseFault, SysCall


UUID = NewType("UUID", str)

LOGGER = logging.getLogger(__name__)


class Configuration:
    """Global faults configuration."""

    syscalls_conf: Dict[UUID, BaseFault] = {}
    syscalls_conf_lock = threading.RLock()

    @classmethod
    def add_fault(cls, uuid: UUID, fault: BaseFault) -> None:
        with cls.syscalls_conf_lock:
            if uuid in cls.syscalls_conf:
                raise ValueError(f"The fault with {uuid=} is set already.")

            if sum(f.probability for f in cls.get_faults_by_syscall_type(fault.sys_call)) + fault.probability > 100:
                raise ValueError(f"Can't add {fault=} with {uuid=} because fault probability for FS call "
                                 f"`{fault.sys_call.value}' will exceed 100%")

            cls.syscalls_conf[uuid] = fault

    @classmethod
    def remove_fault(cls, uuid: UUID) -> Optional[BaseFault]:
        with cls.syscalls_conf_lock:
            return cls.syscalls_conf.pop(uuid, None)

    @classmethod
    def get_fault_by_uuid(cls, uuid: UUID) -> Optional[BaseFault]:
        with cls.syscalls_conf_lock:
            return cls.syscalls_conf.get(uuid)

    @classmethod
    def get_faults_by_syscall_type(cls, syscall_type: SysCall) -> List[BaseFault]:
        with cls.syscalls_conf_lock:
            return [fault for fault in cls.syscalls_conf.values() if fault.sys_call in (syscall_type, SysCall.ALL,)]

    @classmethod
    def get_all_faults_ids(cls) -> List[UUID]:
        with cls.syscalls_conf_lock:
            return list(cls.syscalls_conf.keys())
