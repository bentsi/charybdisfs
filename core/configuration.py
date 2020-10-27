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
        sys.audit("charybdisfs.config", "add_fault", uuid, fault)

        with cls.syscalls_conf_lock:
            if uuid in cls.syscalls_conf:
                raise ValueError(f"The fault with {uuid=} is set already.")

            if fault.sys_call == SysCall.ALL:  # we try to add wildcard syscall, so we need to check all syscalls.
                all_sys_calls = {fault.sys_call for fault in cls.get_all_faults()}
            else:
                all_sys_calls = {fault.sys_call, }

            for sys_call in all_sys_calls:
                faults_by_sys_call = cls.get_faults_by_sys_call(sys_call=sys_call)
                if sum(f.probability for f in faults_by_sys_call) + fault.probability > 100:
                    raise ValueError(f"Can't add {fault=} with {uuid=} because fault probability for FS call "
                                     f"`{sys_call.value}' will exceed 100%")

            cls.syscalls_conf[uuid] = fault

    @classmethod
    def remove_fault(cls, uuid: UUID) -> Optional[BaseFault]:
        sys.audit("charybdisfs.config", "remove_fault", uuid)

        with cls.syscalls_conf_lock:
            return cls.syscalls_conf.pop(uuid, None)

    @classmethod
    def get_fault_by_uuid(cls, uuid: UUID) -> Optional[BaseFault]:
        with cls.syscalls_conf_lock:
            return cls.syscalls_conf.get(uuid)

    @classmethod
    def get_faults_by_sys_call(cls, sys_call: SysCall) -> List[BaseFault]:
        with cls.syscalls_conf_lock:
            # For sys_call == SysCall.ALL it returns faults with exactly SysCall.ALL type, not all.
            return [fault for fault in cls.syscalls_conf.values() if fault.sys_call in (sys_call, SysCall.ALL,)]

    @classmethod
    def get_all_faults(cls) -> List[BaseFault]:
        with cls.syscalls_conf_lock:
            return list(cls.syscalls_conf.values())

    @classmethod
    def get_all_faults_ids(cls) -> List[UUID]:
        with cls.syscalls_conf_lock:
            return list(cls.syscalls_conf.keys())
