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
import json
from enum import Enum


class BaseFault:
    path: str = "*"
    probability: float = 1  # 0-1
    sys_call: Enum
    fault_id: int
    status: Enum
    
    def _serialize(self):
        pass
    
    @classmethod
    def _deserialize(cls, json_repr):
          # return cls.__init__(...)
        pass


class LatencyFault(BaseFault):
    delay: float = 0 # us - microseconds

class ErrorFault(BaseFault):
    error_no: int #errno package
    random: bool

class SysCall(Enum):
    WRITE = "write"
    READ = "read"
    ALL = "*"

class Status(Enum):
    NEW = "new"
    APPLIED = "applied"
