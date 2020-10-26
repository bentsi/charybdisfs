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
from typing import Generic, TypeVar, Type

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


T_fault = TypeVar("T_fault", bound="BaseFault")


class BaseFault(abc.ABC, Generic[T_fault]):
    def __init__(self, sys_call: SysCall, probability: int):
        self.sys_call = sys_call

        assert 0 <= probability <= 100
        self.probability = probability

        self.status = Status.NEW

    def _serialize(self):
        data = self.__dict__
        data["classname"] = type(self).__name__
        data["status"] = data["status"].value
        data["sys_call"] = data["sys_call"].value
        LOGGER.debug("Serialize fault object %s to JSON:\n %s", data["classname"], data)

        return json.dumps(data)

    @classmethod
    def _deserialize(cls: Type[T_fault], json_repr) -> T_fault:
        json_dict: dict = json.loads(json_repr)

        # Remove non-existent parameters
        json_dict.pop('classname', None)

        # Save parameter that not needed for class initialization
        status = Status(json_dict.pop('status'))

        # Convert string to Enum object
        sys_call = SysCall(json_dict.get('sys_call'))
        json_dict['sys_call'] = sys_call

        data = cls(**json_dict)

        data.status = status
        return data

    def apply(self) -> None:
        sys.audit("charybdisfs.fault", self)
        self.status = Status.APPLIED
        self._apply()

    @abc.abstractmethod
    def _apply(self) -> None:
        ...

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(f'{key}={value}' for key, value in self.__dict__.items())})"


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
