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

import wrapt
import pyfuse3


_PYFUSE3_TYPES_TO_WRAP = (
    pyfuse3.EntryAttributes,
    pyfuse3.FileInfo,
    pyfuse3.ReaddirToken,
    pyfuse3.RequestContext,
    pyfuse3.SetattrFields,
    pyfuse3.StatvfsData,
)


class _PyFuse3TypeProxy(wrapt.ObjectProxy):
    def __repr__(self):
        attrs_formatted = ", ".join(f"{attr}={getattr(self, attr)}" for attr in dir(self) if not attr.startswith("__"))
        return f"{self.__class__.__name__}({attrs_formatted})"


def wrap(instance):
    if type(instance) in _PYFUSE3_TYPES_TO_WRAP:
        return _PyFuse3TypeProxy(instance)
    return instance


__all__ = ("wrap",)
