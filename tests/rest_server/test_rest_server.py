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

import time
import errno
import threading

import pytest
import requests

from core.faults import ErrorFault, SysCall
from core.rest_api import start_charybdisfs_api_server, stop_charydisfs_api_server


@pytest.fixture(scope="module")
def start_api_server():
    threading.Thread(target=start_charybdisfs_api_server, daemon=True).start()
    time.sleep(1)
    yield
    stop_charydisfs_api_server()


@pytest.mark.usefixtures("start_api_server")
def test_add_error_fault():
    error_fault = ErrorFault(sys_call=SysCall.WRITE, error_no=errno.ENOSPC, probability=100)
    response = requests.post("http://127.0.0.1:8080/faults", json=error_fault.to_json())
    assert response.ok, f"Failed to add an {error_fault=}: {response.json()}"
