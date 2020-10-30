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

from __future__ import annotations

import abc
import sys
import time
import inspect
import logging
from enum import Enum, auto
from typing import Optional, Dict, Any, Union, NamedTuple, Type, Set, final

from pyfuse3 import FUSEError


LOGGER = logging.getLogger(__name__)


class AutoLowerName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class SysCall(AutoLowerName):
    UNKNOWN = ""
    ACCESS = auto()
    CREATE = auto()
    FLUSH = auto()
    FSYNC = auto()
    FSYNCDIR = auto()
    GETATTR = auto()
    GETXATTR = auto()
    LINK = auto()
    LISTXATTR = auto()
    LOOKUP = auto()
    MKDIR = auto()
    MKNOD = auto()
    OPEN = auto()
    OPENDIR = auto()
    READ = auto()
    READDIR = auto()
    READLINK = auto()
    RELEASE = auto()
    RELEASEDIR = auto()
    REMOVEXATTR = auto()
    RENAME = auto()
    RMDIR = auto()
    SETATTR = auto()
    SETXATTR = auto()
    STATFS = auto()
    SYMLINK = auto()
    WRITE = auto()
    UNLINK = auto()
    ALL = "*"

    @classmethod
    def _missing_(cls, value: str) -> SysCall:
        LOGGER.error("Unknown syscall: %s", value)
        return cls.UNKNOWN


class Status(AutoLowerName):
    NEW = auto()
    APPLIED = auto()

    @classmethod
    def _missing_(cls, value: Optional[str]) -> Status:
        LOGGER.error("Unknown status: %s, return Status.NEW instead", value)
        return cls.NEW


class FaultRegistryItem(NamedTuple):
    fault_type: Type[BaseFault] = None
    fault_args: Set[str] = None


class FaultRegistry(Dict[str, FaultRegistryItem]):
    def __missing__(self, key: str) -> FaultRegistryItem:
        return FaultRegistryItem()


class BaseFault(abc.ABC):
    _fault_registry = FaultRegistry()

    def __init_subclass__(cls):
        cls._fault_registry[cls.__name__] = \
            FaultRegistryItem(fault_type=cls, fault_args=set(inspect.signature(cls).parameters))

    def __init__(self, sys_call: Union[str, SysCall], probability: int):
        self.sys_call = SysCall(sys_call)
        assert self.sys_call != SysCall.UNKNOWN, f"Try to create a fault for an unknown syscall: `{sys_call}'"

        assert 0 <= probability <= 100, "A fault probability should be an integer in the interval [0, 100]"
        self.probability = probability

        self.status = Status.NEW

    @abc.abstractmethod
    def _apply(self) -> None:
        ...

    def apply(self) -> None:
        sys.audit("charybdisfs.fault", self)
        self.status = Status.APPLIED
        self._apply()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fault_type": type(self).__name__,
            **vars(self),
            "sys_call": self.sys_call.value,
            "status": self.status.value,
        }

    @classmethod
    @final
    def from_dict(cls, data: Dict[str, Any]) -> Optional[BaseFault]:
        fault_type_name = data.get("fault_type")
        fault_type, fault_args = cls._fault_registry[fault_type_name]

        if fault_type is None:
            LOGGER.error("Unknown fault type: %s", fault_type_name)
            return None

        try:
            fault = fault_type(**{arg: data[arg] for arg in set(data) & fault_args})
        except TypeError as exc:
            LOGGER.error("Unable to create a %s object: %s", fault_type_name, exc)
            return None

        fault.update_internal_state_from_dict(data)

        return fault

    def update_internal_state_from_dict(self, data: Dict[str, Any]) -> None:
        self.status = Status(data.get("status"))

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(f'{key}={value}' for key, value in self.__dict__.items())})"

    def __eq__(self, other):
        return type(self) == type(other) and vars(self) == vars(other)


class LatencyFault(BaseFault):
    def __init__(self, sys_call: Union[str, SysCall], probability: int, delay: float = 0):
        super().__init__(sys_call=sys_call, probability=probability)
        self.delay = delay  # us - microseconds

    def _apply(self) -> None:
        time.sleep(self.delay / 1e6)


class ErrorFault(BaseFault):
    def __init__(self, sys_call: Union[str, SysCall], probability: int, error_no: int):
        super().__init__(sys_call=sys_call, probability=probability)
        self.error_no = error_no

    def _apply(self) -> None:
        raise FUSEError(self.error_no)


def create_fault_from_dict(data: Dict[str, Any]) -> Optional[BaseFault]:
    return BaseFault.from_dict(data=data)
