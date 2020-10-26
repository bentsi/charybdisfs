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
import uuid
import errno
import logging
from threading import Thread

import trio
import click
import pyfuse3

from core.faults import ErrorFault, SysCall
from core.operations import CharybdisOperations
from core.configuration import Configuration
from core.rest_api import rest_start, rest_stop


LOGGER = logging.getLogger("charybdisfs")


def sys_audit_hook(name, args):
    if name == "charybdisfs.syscall":
        LOGGER.debug("CharybdisFS call made: name=%s, args=%s, kwargs=%s", args[0], args[1], args[2])
    if name == "charybdisfs.fault":
        LOGGER.debug("CharybdisFS fault applied: %s", args[0])
    elif name.startswith("os."):
        LOGGER.debug("os call made: name=%s, args=%s", name[3:], args)


@click.command()
@click.option('--debug/--no-debug', default=False)
@click.option('--enospc-probability', type=float, default=0.1)
@click.argument("source", type=str)
@click.argument("target", type=str)
def start_charybdisfs(source: str, target: str, debug: bool, enospc_probability: float) -> None:
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG if debug else logging.INFO,
                        format=">>> %(asctime)s -%(levelname).1s- %(name)s  %(message)s")
    if debug:
        sys.addaudithook(sys_audit_hook)

    # Add ENOSPC fault to any FS call statically.  Should be removed in final version.
    enospc_probability = max(0, min(100, round(enospc_probability * 100)))
    LOGGER.info("Going to add ENOSPC fault with probability %s%%", enospc_probability)
    enospc_fault = ErrorFault(sys_call=SysCall.ALL, probability=enospc_probability, error_no=errno.ENOSPC)
    Configuration.add_fault(uuid=str(uuid.uuid4()), fault=enospc_fault)
    LOGGER.debug("Faults added: %s", Configuration.get_all_faults())

    operations = CharybdisOperations(source=source)

    fuse_options = set(pyfuse3.default_options)
    fuse_options.add("fsname=charybdisfs")
    if debug:
        fuse_options.add("debug")

    server_thread = Thread(target=rest_start, daemon=True)
    server_thread.start()

    pyfuse3.init(operations, target, fuse_options)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=False)
        rest_stop()
        raise
    pyfuse3.close()
    rest_stop()

start_charybdisfs(prog_name="charybdisfs")
