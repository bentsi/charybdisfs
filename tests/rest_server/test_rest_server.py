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

import pytest
import requests

from core.faults import ErrorFault, SysCall
from core.rest_api import start_charybdisfs_api_server


# server bingup in other process
#@pytest.fixture(scope="module")
# def rest_server():
#     start_charybdisfs_api_server()


@pytest.mark.skip(reason='first need pass on deserialize')
def test_add_error_fault():
    error_fault = ErrorFault(sys_call=SysCall.WRITE, error_no=errno.ENOSPC, probability=100)
    s = requests.Session()
    base = 'http://127.0.0.1:8080/'
    resource = 'faults'
    try:
        json_obj = error_fault.to_json()

        response = s.post(f'{base}{resource}', json=json_obj)
        if response.status_code != 200:
            error_string = f"Failed to send fault ={errno}. Returned {response.json()}"
            raise ValueError(error_string)
    except Exception as e:
        print(f"Exception {e}")
        raise
    assert(response.status_code == 200)
