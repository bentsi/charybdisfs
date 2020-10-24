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

from core.operations import PathMapping


@pytest.fixture
def mapping():
    return PathMapping("/")


def test_get_from_empty(mapping):
    with pytest.raises(KeyError):
        path = mapping[42]


def test_set_one_path(mapping):
    mapping[42] = "/root"
    assert mapping[42] == "/root"
    assert mapping.lookups[42] == 1


def test_set_many_paths(mapping):
    mapping[42] = "/root"
    mapping[42] = "/home"
    mapping[42] = "/lib"
    assert mapping[42] in ["/root", "/home", "/lib"]
    assert mapping.lookups[42] == 3
    assert dict.__getitem__(mapping, 42) == {"/root", "/home", "/lib"}


def test_set_same_path_twice(mapping):
    mapping[42] = "/root"
    mapping[42] = "/root"
    assert mapping[42] == "/root"
    assert mapping.lookups[42] == 2
    assert dict.__getitem__(mapping, 42) == "/root"


def test_forget(mapping):
    mapping[42] = "/root"
    mapping[42] = "/root"
    mapping[42] = "/root"

    mapping.forget(inode=42, nlookup=2)
    assert 42 in mapping
    assert mapping.lookups[42] == 1

    mapping.forget(inode=42, nlookup=1)
    assert 42 not in mapping
    assert 42 not in mapping.lookups

    mapping[13] = "/lib"

    mapping.forget(inode=13, nlookup=666)
    assert 13 not in mapping
    assert 13 not in mapping.lookups
