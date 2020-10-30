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
import threading

import pytest

from core.rest_api import start_charybdisfs_api_server, stop_charybdisfs_api_server, DEFAULT_PORT
from client import CharybdisFsClient


@pytest.fixture(scope="module")
def start_api_server():
    threading.Thread(target=start_charybdisfs_api_server, daemon=True).start()
    time.sleep(1)
    yield
    stop_charybdisfs_api_server()


@pytest.fixture(scope="module")
def faults_api_url() -> str:
    return f"http://127.0.0.1:{DEFAULT_PORT}/faults"


@pytest.fixture
def api_client() -> CharybdisFsClient:
    return CharybdisFsClient(host="127.0.0.1", port=DEFAULT_PORT)
