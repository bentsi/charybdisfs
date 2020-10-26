#!/usr/bin/env python3
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

import sys
import logging

import trio
import click
import pyfuse3

from core.operations import CharybdisOperations


LOGGER = logging.getLogger("charybdisfs")


def sys_audit_hook(name, args):
    if name == "charybdisfs":
        LOGGER.debug("CharybdisFS call made: name=%s, args=%s, kwargs=%s", args[0], args[1], args[2])
    elif name.startswith("os."):
        LOGGER.debug("os call made: name=%s, args=%s", name[3:], args)


@click.command()
@click.option('--debug/--no-debug', default=False)
@click.option('--enospc-probability', type=float, default=0.1)
@click.argument("source", type=str)
@click.argument("target", type=str)
def start_charybdisfs(source: str, target: str, debug: bool, enospc_probability) -> None:
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG if debug else logging.INFO,
                        format=">>> %(asctime)s -%(levelname).1s- %(name)s  %(message)s")
    if debug:
        sys.addaudithook(sys_audit_hook)

    operations = CharybdisOperations(source=source, enospc_probability=enospc_probability)

    fuse_options = set(pyfuse3.default_options)
    fuse_options.add("fsname=charybdisfs")
    if debug:
        fuse_options.add("debug")

    pyfuse3.init(operations, target, fuse_options)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=False)
        raise
    pyfuse3.close()


start_charybdisfs(prog_name="charybdisfs")
