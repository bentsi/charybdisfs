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
import json
import logging
from enum import Enum
from typing import Generic, TypeVar, Type, Optional, final

from pyfuse3 import FUSEError


LOGGER = logging.getLogger(__name__)


class SysCall(Enum):
    UNKNOWN = ""
    ACCESS = "access"
    CREATE = "create"
    FORGET = "forget"
    FLUSH = "flush"
    FSYNC = "fsync"
    FSYNCDIR = "fsyncdir"
    GETATTR = "getattr"
    GETXATTR = "getxattr"
    LINK = "link"
    LISTXATTR = "listxattr"
    LOOKUP = "lookup"
    MKDIR = "mkdir"
    MKNOD = "mknod"
    OPEN = "open"
    OPENDIR = "opendir"
    READ = "read"
    READDIR = "readdir"
    READLINK = "readlink"
    RELEASE = "release"
    RELEASEDIR = "releasedir"
    REMOVEXATTR = "removexattr"
    RENAME = "rename"
    RMDIR = "rmdir"
    SETATTR = "setattr"
    SETXATTR = "setxattr"
    STATFS = "statfs"
    SYMLINK = "symlink"
    WRITE = "write"
    UNLINK = "unlink"
    ALL = "*"

    @classmethod
    def _missing_(cls, value: str) -> SysCall:
        LOGGER.error("Unknown syscall: %s", value)
        return cls.UNKNOWN


class Status(Enum):
    NEW = "new"
    APPLIED = "applied"

    @classmethod
    def _missing_(cls, value: Optional[str]) -> Status:
        LOGGER.error("Unknown status: %s, return Status.NEW instead", value)
        return cls.NEW


T_fault = TypeVar("T_fault", bound="BaseFault")


class BaseFault(abc.ABC, Generic[T_fault]):
    _fault_registry = {}

    def __init_subclass__(cls):
        cls._fault_registry[cls.__name__] = cls

    def __init__(self, sys_call: SysCall, probability: int):
        self.sys_call = sys_call

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

    def to_json(self) -> str:
        data = {
            "fault_type": type(self).__name__,
            **vars(self),
            "sys_call": self.sys_call.value,
            "status": self.status.value,
        }
        LOGGER.debug("%s object serialized to JSON: %s", data["fault_type"], data)
        return json.dumps(data)

    @classmethod
    def from_dict(cls: Type[T_fault], data: dict) -> Optional[T_fault]:
        status = Status(data.pop("status", None))
        data["sys_call"] = SysCall(data.get("sys_call"))
        try:
            fault = cls(**data)
        except TypeError:
            LOGGER.error("Unable to create a %s object from params: %s", cls.__name__, data)
            return None
        fault.status = status
        return fault

    @final
    @classmethod
    def from_json(cls, json_data: str) -> Optional[BaseFault]:
        try:
            return json.loads(json_data, object_hook=cls._json_object_hook)
        except json.JSONDecodeError as exc:
            LOGGER.error("Unable to decode a JSON data: %s", exc)
            return None

    @classmethod
    def _json_object_hook(cls, data: dict) -> Optional[BaseFault]:
        if (fault_type := cls._fault_registry.get(data.pop("fault_type", None))) is None:
            LOGGER.error("Unable to create a fault object from a JSON data: %s", data)
            return None
        return fault_type.from_dict(data)

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(f'{key}={value}' for key, value in self.__dict__.items())})"

    def __eq__(self, other):
        return type(self) == type(other) and vars(self) == vars(other)


class LatencyFault(BaseFault):
    def __init__(self, sys_call: SysCall, probability: int, delay: float = 0):
        super().__init__(sys_call=sys_call, probability=probability)
        self.delay = delay  # us - microseconds

    def _apply(self) -> None:
        time.sleep(self.delay / 1e6)


class ErrorFault(BaseFault):
    def __init__(self, sys_call: SysCall, probability: int, error_no: int):
        super().__init__(sys_call=sys_call, probability=probability)
        self.error_no = error_no

    def _apply(self) -> None:
        raise FUSEError(self.error_no)


def create_fault_from_json(json_data: str) -> BaseFault:
    return BaseFault.from_json(json_data=json_data)
