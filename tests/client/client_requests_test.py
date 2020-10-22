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

import unittest

from client.client import CharybdisFsClient


class ClientRequestTest(unittest.TestCase):

    def test_correct_url(self):
        with CharybdisFsClient() as fs_client:
            request_status = fs_client.send_request(host="www.python.org", method='GET', json="", use_https=True)

        self.assertTrue(request_status.status_code == 200,
                        f'Unexpected response: status {request_status.status_code}; Text: {request_status.text}')

    def test_correct_url_wrong_data(self):
        with CharybdisFsClient() as fs_client:
            request_status = fs_client.send_request(host="google.com", method='GET', json="requests", use_https=True)

        self.assertTrue(request_status.status_code == 400,
                        f'Unexpected response: status {request_status.status_code}; Text: {request_status.text}')

    def test_wrong_url(self):
        last_exc = None
        with CharybdisFsClient() as fs_client:
            try:
                _ = fs_client.send_request(host="127.0.0.1", method='GET', json="scylla", use_https=True)
            except Exception as exc:
                last_exc = exc

        self.assertTrue(last_exc,
                        f'Unexpected response: {str(last_exc)}')

if __name__ == '__main__':
    unittest.main()
