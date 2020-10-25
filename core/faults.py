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
from enum import Enum


class SysCall(Enum):
    WRITE = "write"
    READ = "read"
    ALL = "*"


class Status(Enum):
    NEW = "new"
    APPLIED = "applied"


class BaseFault:
    def __init__(self, sys_call: SysCall, path: str = "*", probability: float = 1):
        self.path = path
        self.probability = probability  # 0-1
        self.sys_call = sys_call.value
    
    def _serialize(self):
        data = self.__dict__
        data.update({'classname': self.__class__.__name__})
        return json.dumps(data)
    
    @classmethod
    def _deserialize(cls, json_repr):
        return cls(**json.loads(json_repr))


class LatencyFault(BaseFault):
    def __init__(self, sys_call: SysCall, path: str = "*", probability: float = 1,
                 delay: float = 0):
        self.delay = delay # us - microseconds
        super(LatencyFault, self).__init__(sys_call, path, probability)

class ErrorFault(BaseFault):
    def __init__(self, error_no: int, random: bool, sys_call: SysCall, path: str = "*",
                 probability: float = 1):
        self.error_no = error_no
        self.random = random
        super(ErrorFault, self).__init__(sys_call, path, probability)
