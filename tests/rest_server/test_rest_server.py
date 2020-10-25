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

import pytest
import requests
import errno
from core.rest_api import rest_start
from core.faults import LatencyFault, ErrorFault, SysCall, Status


@pytest.fixture(scope="module")
def rest_server():
    return rest_start()

def test_add_error_fault():
    error_fault = ErrorFault(sys_call = SysCall.WRITE, status= Status.NEW, error_no=errno.ENOSPC, randon=False)
    s = requests.Session()
    base = 'http://127.0.0.1:8080/'
    resource = 'faults'
    try:
        response = s.post(f'{base}{resource}', json=error_fault._serialize())
        if response.status_code != 200:
            raise ValueError(f"Failed to send fault ={errno}. Returned {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Exception {e}")
