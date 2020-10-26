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

class Configuration:
    syscalls_conf = {}

    @classmethod
    def set_fault(cls, uuid, fault):
        cls.syscalls_conf.update({uuid: fault})

    @classmethod
    def remove_fault(cls, uuid):
        if cls.get_fault(uuid):
            cls.syscalls_conf.pop(uuid)
            return uuid
        else:
            return 0

    @classmethod
    def get_fault(cls, uuid):
        return cls.syscalls.get(uuid, None)

    @classmethod
    def get_all_faults_ids(cls):
        return list(cls.syscalls.keys())

    def set_all_fault(self):
        pass
