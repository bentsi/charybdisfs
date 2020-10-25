# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2020 ScyllaDB


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
