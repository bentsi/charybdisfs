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
    assert mapping.inode_lookups[42] == 1


def test_set_many_paths(mapping):
    mapping[42] = "/root"
    mapping[42] = "/home"
    mapping[42] = "/lib"
    assert mapping[42] in ["/root", "/home", "/lib"]
    assert mapping.inode_lookups[42] == 3
    assert dict.__getitem__(mapping, 42) == {"/root", "/home", "/lib"}


def test_set_same_path_twice(mapping):
    mapping[42] = "/root"
    mapping[42] = "/root"
    assert mapping[42] == "/root"
    assert mapping.inode_lookups[42] == 2
    assert dict.__getitem__(mapping, 42) == "/root"


def test_forget_path(mapping):
    mapping[42] = "/root"
    mapping[42] = "/home"
    mapping[42] = "/lib"

    with pytest.raises(KeyError):
        mapping.forget_path(42, "/usr")
    assert dict.__getitem__(mapping, 42) == {"/root", "/home", "/lib"}
    assert mapping.inode_lookups[42] == 3

    mapping.forget_path(100500, "/root")
    assert dict.__getitem__(mapping, 42) == {"/root", "/home", "/lib"}
    assert mapping.inode_lookups[42] == 3

    mapping.forget_path(42, "/root")
    assert dict.__getitem__(mapping, 42) == {"/home", "/lib"}
    assert mapping.inode_lookups[42] == 3

    mapping.forget_path(42, "/home")
    assert dict.__getitem__(mapping, 42) == "/lib"
    assert mapping.inode_lookups[42] == 3

    with pytest.raises(KeyError):
        mapping.forget_path(42, "/usr")
    assert dict.__getitem__(mapping, 42) == "/lib"
    assert mapping.inode_lookups[42] == 3

    mapping.forget_path(42, "/lib")
    assert 42 not in mapping
    assert mapping.inode_lookups[42] == 3


def test_forget_path_and_add_again(mapping):
    mapping[42] = "/root"
    mapping.forget_path(42, "/root")
    assert mapping.inode_lookups[42] == 1
    mapping[42] = "/root"
    assert mapping.inode_lookups[42] == 2  # is it expected?


def replace_path_for_inode_with_one_path(mapping):
    mapping[42] = "/root"

    mapping.replace_path(100500, "/root", "/usr")
    assert dict.__getitem__(mapping, 42) == "/root"
    assert mapping.inode_lookups[42] == 1

    with pytest.raises(KeyError):
        mapping.replace_path(42, "/lib", "/usr")
    assert dict.__getitem__(mapping, 42) == "/root"
    assert mapping.inode_lookups[42] == 1

    mapping.replace_path(42, "/root", "/usr")
    assert dict.__getitem__(mapping, 42) == "/usr"
    assert mapping.inode_lookups[42] == 1


def replace_path_for_inode_with_multiple_pathes(mapping):
    mapping[42] = "/root"
    mapping[42] = "/home"

    mapping.replace_path(100500, "/root", "/usr")
    assert dict.__getitem__(mapping, 42) == {"/root", "/home"}
    assert mapping.inode_lookups[42] == 2

    with pytest.raises(KeyError):
        mapping.replace_path(42, "/lib", "/usr")
    assert dict.__getitem__(mapping, 42) == {"/root", "/home"}
    assert mapping.inode_lookups[42] == 2

    mapping.replace_path(42, "/root", "/usr")
    assert dict.__getitem__(mapping, 42) == {"/usr", "/home"}
    assert mapping.inode_lookups[42] == 2


def test_forget_inode_lookups(mapping):
    mapping[42] = "/root"
    mapping[42] = "/root"
    mapping[42] = "/root"

    mapping.forget_inode_lookups(inode=42, nlookup=2)
    assert 42 in mapping
    assert mapping.inode_lookups[42] == 1

    mapping.forget_inode_lookups(inode=42, nlookup=1)
    assert 42 not in mapping
    assert 42 not in mapping.inode_lookups

    mapping[13] = "/lib"

    mapping.forget_inode_lookups(inode=13, nlookup=666)
    assert 13 not in mapping
    assert 13 not in mapping.inode_lookups
