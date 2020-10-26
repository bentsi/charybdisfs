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
import json
from core.rest_api import rest_start
from core.faults import LatencyFault, ErrorFault, SysCall, Status
import core

# server bingup in other process
#@pytest.fixture(scope="module")
#def rest_server():
#    return rest_start()


@pytest.mark.skip(reason="testing with server")
def test_error_fault_deserialize_directly():
    error_fault = ErrorFault(sys_call=SysCall(SysCall.WRITE), error_no=errno.ENOSPC, probability=100)
    json_obj = error_fault._serialize()
    jsonloaded = json.loads(json_obj)
    cls = jsonloaded.get('classname', None)
    if cls is None:
        print(f'did not foud classname field in json')
        return None
    print(cls)
    clsptr = getattr(core.faults, cls)
    jsonloaded.pop('classname')
    if 'fault_id' in jsonloaded:
        jsonloaded.pop('fault_id')
    if clsptr is None:
        print(f'did not found class {cls}')
        return None
    fault = None
    try:
        fault = clsptr._deserialize(json.dumps(jsonloaded))
    except BaseException as ex:
        print(f"exception {ex} when trying to deserialize {jsonloaded} cls={cls}")
        print("FIX EXCEPTION")
    return fault


@pytest.mark.skip(reason='first need pass on deserialize')
def test_add_error_fault():
    error_fault = ErrorFault(sys_call=SysCall.WRITE, error_no=errno.ENOSPC, probability=100)
    s = requests.Session()
    base = 'http://127.0.0.1:8080/'
    resource = 'faults'
    try:
        json_obj = error_fault._serialize()

        response = s.post(f'{base}{resource}', json=json_obj)
        if response.status_code != 200:
            error_string = f"Failed to send fault ={errno}. Returned {response.json()}"
            raise ValueError(error_string)
    except Exception as e:
        print(f"Exception {e}")
        raise
    assert(response.status_code == 200)
