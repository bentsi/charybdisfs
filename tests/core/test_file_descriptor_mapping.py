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

from core.operations import FileDescriptorMapping


@pytest.fixture
def mapping():
    return FileDescriptorMapping()


def test_get_from_empty(mapping):
    with pytest.raises(KeyError):
        path = mapping[42]


def test_set_once(mapping):
    mapping[42] = 100500
    assert mapping[42] == 100500
    assert mapping.inodes[100500] == 42
    assert mapping.open_counters[100500] == 1


def test_set_twice(mapping):
    mapping[42] = 100500
    with pytest.raises(ValueError):
        mapping[42] = 100500
    assert mapping[42] == 100500
    assert mapping.inodes[100500] == 42
    assert mapping.open_counters[100500] == 1


def test_del(mapping):
    mapping[42] = 100500

    del mapping[42]
    assert 42 not in mapping
    assert 100500 not in mapping.inodes
    assert 100500 not in mapping.open_counters


def test_acquire_release(mapping):
    mapping[42] = 100500

    mapping.acquire(100500)
    assert mapping[42] == 100500
    assert mapping.inodes[100500] == 42
    assert mapping.open_counters[100500] == 2

    assert not mapping.release(100500)
    assert mapping[42] == 100500
    assert mapping.inodes[100500] == 42
    assert mapping.open_counters[100500] == 1

    assert mapping.release(100500)
    assert 42 not in mapping
    assert 100500 not in mapping.inodes
    assert 100500 not in mapping.open_counters


def test_acquire_by_inode(mapping):
    assert mapping.acquire_by_inode(42) is None
    assert 42 not in mapping
    assert 42 not in mapping.inodes

    mapping[42] = 100500
    assert mapping.acquire_by_inode(42) == 100500
    assert mapping.open_counters[100500] == 2
