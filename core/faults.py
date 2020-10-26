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
import json
import logging
import time
from enum import Enum
from pyfuse3 import FUSEError

LOGGER = logging.getLogger(__name__)


class SysCall(Enum):
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


class Status(Enum):
    NEW = "new"
    APPLIED = "applied"


class BaseFault:
    def __init__(self, sys_call: SysCall, probability: int):
        assert 0 <= probability <= 100
        self.probability = probability
        self.sys_call = sys_call.value
        self.status = Status.NEW
    
    def _serialize(self):
        data = self.__dict__
        data.update({'classname': self.__class__.__name__})
        LOGGER.debug("Serialize fault object %s to json:\n %s", self.__class__.__name__, str(data))
        return json.dumps(data)

    @classmethod
    def _deserialize(cls, json_repr):
        return cls(**json.loads(json_repr))

    def apply(self) -> None:
        raise NotImplementedError


class LatencyFault(BaseFault):
    def __init__(self, sys_call: SysCall, probability: int, delay: float = 0):
        self.delay = delay  # us - microseconds
        super().__init__(sys_call=sys_call, probability=probability)

    def apply(self) -> None:
        time.sleep(self.delay / 1e6)
        self.status = Status.APPLIED


class ErrorFault(BaseFault):
    def __init__(self, sys_call: SysCall, probability: int, error_no: int):
        self.error_no = error_no
        super().__init__(sys_call=sys_call, probability=probability)

    def apply(self) -> None:
        self.status = Status.APPLIED
        raise FUSEError(self.error_no)
