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

from __future__ import annotations

import logging
from typing import List, Tuple, Optional, NewType, Literal

from requests import Session, Request, Response

from core.faults import BaseFault


LOGGER = logging.getLogger(__name__)


FaultID = NewType("FaultID", str)


class CharybdisFsClient:
    rest_resource = "faults"

    def __init__(self, host: str, port: int, timeout: int = 10, use_https: bool = False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_https = use_https

        self.base_url = f"{'https' if self.use_https else 'http'}://{self.host}:{self.port}"
        self.active_faults: List[FaultID] = []

        self._session = Session()

    def __enter__(self) -> CharybdisFsClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove_all_active_faults()
        self.close()

    def close(self) -> None:
        self._session.close()

    def send_request(self,
                     method: Literal["GET", "POST", "DELETE"] = "GET",
                     fault_id: FaultID = FaultID(""),
                     data: Optional[dict] = None) -> Response:
        url = f"{self.base_url}/{self.rest_resource}/{fault_id}".rstrip("/")

        LOGGER.debug("Send request to %s with data: %s", url, data)
        req = Request(method=method, url=url, json=data)
        prepped_request = self._session.prepare_request(request=req)
        response = self._session.send(request=prepped_request, timeout=self.timeout)

        LOGGER.debug("Response status: %s; reason: %s", response.status_code, response.reason)
        return response

    def add_fault(self, fault: BaseFault) -> Tuple[FaultID, Response]:
        response = self.send_request(method="POST", data=fault.to_dict())

        if not response.ok:
            return FaultID(""), response

        if fault_id := FaultID(response.json().get("fault_id", "")):
            self.active_faults.append(fault_id)

        return fault_id, response

    def remove_fault(self, fault_id: FaultID) -> Response:
        response = self.send_request(method="DELETE", fault_id=fault_id)

        if response.ok:
            self.active_faults.remove(fault_id)

        return response

    def get_active_faults(self) -> Response:
        return self.send_request()

    def remove_all_active_faults(self) -> None:
        for fault_id in self.active_faults:
            self.remove_fault(fault_id=fault_id)
