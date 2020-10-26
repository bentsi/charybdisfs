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
import unittest

from threading import Thread

from core.rest_api import DEFAULT_PORT, rest_start
from client.client import CharybdisFsClient
from core.faults import LatencyFault, ErrorFault, SysCall


class ClientRequestTest(unittest.TestCase):
    server_thread = None

    @classmethod
    def setUp(cls):
        cls.server_thread = cls.run_server()

    @staticmethod
    def run_server():
        server_thread = Thread(target=rest_start, daemon=True)
        server_thread.start()
        return server_thread

    def test_latency(self):
        with CharybdisFsClient('127.0.0.1', DEFAULT_PORT) as fs_client:
            latency_fault = LatencyFault(sys_call=SysCall.WRITE, probability=100, delay=1000)
            fault_id, response = fs_client.add_fault(fault=latency_fault)

        self.assertTrue(response.status_code == 200,
                        f'Request failed. Status: {response.status_code}\n Text: {response.text}')

    def test_error(self):
        with CharybdisFsClient('127.0.0.1', DEFAULT_PORT) as fs_client:
            error_fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.EADV)
            fault_id, response = fs_client.add_fault(fault=error_fault)

        self.assertTrue(response.status_code == 200,
                        f'Request failed. Status: {response.status_code}\n Text: {response.text}')

    def test_serialize(self):
        latency_fault = LatencyFault(sys_call=SysCall.WRITE, probability=100, delay=1000)
        serialized = latency_fault._serialize()

        self.assertTrue(serialized == '{"delay": 1000, "probability": 100, "sys_call": "write", "status": "new", '
                                      '"classname": "LatencyFault"}')

    def test_deserialize(self):
        latency_fault = LatencyFault(sys_call=SysCall.WRITE, probability=100, delay=1000)
        serialized = latency_fault._serialize()
        deserialized = latency_fault._deserialize(serialized)

        self.assertTrue(isinstance(deserialized, LatencyFault))

if __name__ == '__main__':
    unittest.main()
