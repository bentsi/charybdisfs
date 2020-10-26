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
import atexit
import logging
import threading

import trio
import click
import pyfuse3

from core.faults import ErrorFault, SysCall
from core.rest_api import rest_start, rest_stop, DEFAULT_PORT
from core.operations import CharybdisOperations
from core.configuration import Configuration
from core.pyfuse3_types import wrap as pyfuse3_types_wrap


LOGGER = logging.getLogger("charybdisfs")
AUDIT = logging.getLogger("charybdisfs.audit")


def sys_audit_hook(name, args):
    if name == "charybdisfs.syscall":
        AUDIT.debug(
            "CharybdisFS call made: name=%s, args=%s, kwargs=%s",
            args[0],
            [pyfuse3_types_wrap(arg) for arg in args[1]],
            {arg: pyfuse3_types_wrap(value) for arg, value in args[2].items()}
        )
    elif name == "charybdisfs.fault":
        AUDIT.debug("CharybdisFS fault applied: %s", args[0])
    elif name == "charybdisfs.config":
        AUDIT.debug("CharybdisFS configuration call `%s' made with args=%s", args[0], args[1:])
    elif name.startswith("os."):
        AUDIT.debug("os call made: name=%s, args=%s", name[3:], args)


@click.command()
@click.option('--debug/--no-debug', default=False)
@click.option('--rest-api/--no-rest-api', default=True)
@click.option('--rest-api-port', type=int, default=DEFAULT_PORT)
@click.option('--mount/--no-mount', default=True)
@click.option('--static-enospc/--no-static-enospc', default=False)
@click.option('--static-enospc-probability', type=float, default=0.1)
@click.argument("source", type=click.Path(exists=True, dir_okay=True), required=False)
@click.argument("target", type=click.Path(exists=True, dir_okay=True), required=False)
def start_charybdisfs(source: str,
                      target: str,
                      debug: bool,
                      rest_api: bool,
                      rest_api_port: int,
                      mount: bool,
                      static_enospc: bool,
                      static_enospc_probability: float) -> None:
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG if debug else logging.INFO,
                        format=">>> %(asctime)s -%(levelname).1s- %(name)s  %(message)s")

    if not rest_api and not mount:
        raise click.UsageError(message="can't run --no-rest-api and --no-mount simultaneously")

    if debug:
        sys.addaudithook(sys_audit_hook)

    if static_enospc:
        static_enospc_probability = max(0, min(100, round(static_enospc_probability * 100)))
        LOGGER.info("Going to add ENOSPC fault for all syscalls with probability %s%%", static_enospc_probability)
        enospc_fault = ErrorFault(sys_call=SysCall.ALL, probability=static_enospc_probability, error_no=errno.ENOSPC)
        Configuration.add_fault(uuid=str(uuid.uuid4()), fault=enospc_fault)
        LOGGER.debug("Faults added: %s", Configuration.get_all_faults())

    if rest_api:
        server_thread = threading.Thread(target=rest_start, kwargs={"port": rest_api_port,}, daemon=True)
        server_thread.start()
        atexit.register(rest_stop)

    if mount:
        if source is None or target is None:
            raise click.BadArgumentUsage("both source and target parameters are required for CharybdisFS mount")

        fuse_options = set(pyfuse3.default_options)
        fuse_options.add("fsname=charybdisfs")
        if debug:
            fuse_options.add("debug")

        operations = CharybdisOperations(source=source)

        pyfuse3.init(operations, target, fuse_options)
        atexit.register(pyfuse3.close)

    try:
        if mount:
            trio.run(pyfuse3.main)
        else:
            server_thread.join()
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user...")
        sys.exit(0)


if __name__ == "__main__":
    start_charybdisfs(prog_name="charybdisfs")
