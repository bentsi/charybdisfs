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

import os
from typing import NewType, List, Tuple, Literal, Sequence, Dict, Optional
from collections import Counter

from pyfuse3 import \
    Operations, RequestContext, EntryAttributes, SetattrFields, FileInfo, StatvfsData, ReaddirToken, FUSEError, \
    RENAME_EXCHANGE, RENAME_NOREPLACE, ROOT_INODE


INode = NewType("INode", int)
INodeList = List[Tuple[INode, int]]
FileDescriptor = NewType("FileDescriptor", int)
FileHandle = NewType("FileHandle", int)
FileMode = NewType("FileMode", int)
RenameFlags = Literal[RENAME_EXCHANGE, RENAME_NOREPLACE]


class PathMapping(Dict[INode, str]):
    def __init__(self, root):
        super().__init__({ROOT_INODE: root, })

    def __getitem__(self, inode: INode) -> str:
        path = super().__getitem__(inode)
        if isinstance(path, set):
            for path in path:
                break
        return path

    def __setitem__(self, inode: INode, path: str) -> None:
        if (old_path := super().get(inode)) is not None:
            if isinstance(old_path, set):
                old_path.add(path)
            else:
                super().__setitem__(inode, {old_path, path})
        else:
            super().__setitem__(inode, path)


class FileDescriptorMapping(Dict[INode, FileDescriptor]):
    def __init__(self):
        super().__init__()
        self.inodes: Dict[FileDescriptor, INode] = {}
        self.counters = Counter()

    def __setitem__(self, inode, fd):
        if inode in self:
            raise ValueError("Can't assign same inode twice")
        super().__setitem__(inode, fd)
        self.inodes[fd] = inode
        self.counters[fd] = 1

    def __delitem__(self, inode):
        del self.inodes[(fd := super().pop(inode))]
        del self.counters[fd]

    def acquire_by_inode(self, inode: INode) -> Optional[FileDescriptor]:
        if (fd := self.get(inode)) is not None:
            self.counters[fd] += 1
        return fd

    def acquire(self, fd: FileDescriptor) -> None:
        self.counters[fd] += 1

    def release(self, fd: FileDescriptor) -> None:
        if self.counters[fd] == 1:
            del self[self.inodes[fd]]
        else:
            self.counters[fd] -= 1


class CharybdisOperations(Operations):
    enable_writeback_cache = True

    def __init__(self, source: str):
        super().__init__()
        self.paths = PathMapping(root=source)
        self.descriptors = FileDescriptorMapping()

    async def access(self, inode: INode, mode: FileMode, ctx: RequestContext) -> bool:
        return os.access(self.paths[inode], mode=mode)

    async def create(self,
                     parent_inode: INode,
                     name: str,
                     mode: FileMode,
                     flags: int,
                     ctx: RequestContext) -> Tuple[FileInfo, EntryAttributes]:
        ...

    async def forget(self, inode_list: INodeList) -> None:
        ...

    async def flush(self, fh: FileHandle) -> None:
        ...

    async def fsync(self, fh: INode, datasync: bool) -> None:
        ...

    async def fsyncdir(self, fh: FileHandle, datasync: bool) -> None:
        ...

    async def getattr(self, inode: INode, ctx: RequestContext) -> EntryAttributes:
        ...

    async def getxattr(self, inode: INode, name: bytes, ctx: RequestContext) -> bytes:
        ...

    async def link(self, inode: INode, new_parent_inode: INode, new_name: str, ctx: RequestContext) -> EntryAttributes:
        ...

    async def listxattr(self, inode: INode, ctx: RequestContext) -> Sequence[bytes]:
        ...

    async def lookup(self, parent_inode: INode, name: str, ctx: RequestContext) -> INode:
        ...

    async def mkdir(self, parent_inode: INode, name: str, mode: FileMode, ctx: RequestContext) -> EntryAttributes:
        ...

    async def mknod(self,
                    parent_inode: INode,
                    name: str,
                    mode: FileMode,
                    rdev: int,
                    ctx: RequestContext) -> EntryAttributes:
        ...

    async def open(self, inode: INode, flags: int, ctx: RequestContext) -> FileInfo:
        if (fd := self.descriptors.acquire_by_inode(inode)) is None:
            if flags & os.O_CREAT:
                raise ValueError("Found O_CREAT in flags")
            try:
                fd = os.open(self.paths[inode], flags)
            except OSError as exc:
                raise FUSEError(exc.errno) from None
            self.descriptors[inode] = fd
        return FileInfo(fh=fd)

    async def opendir(self, inode: INode, ctx: RequestContext) -> FileHandle:
        ...

    async def read(self, fd: FileHandle, offset: int, length: int) -> bytes:
        ...

    async def readdir(self, inode: INode, start_id: int, token: ReaddirToken) -> None:
        ...

    async def readlink(self, inode: INode, ctx: RequestContext) -> INode:
        ...

    async def release(self, fd: FileHandle) -> None:
        ...

    async def releasdir(self, fh: FileHandle) -> None:
        ...

    async def removexattr(self, inode: INode, name: bytes, ctx: RequestContext) -> None:
        ...

    async def rename(self,
                     rename_inode_old: INode,
                     name_old: str,
                     parent_inode_new: INode,
                     name_new: str,
                     flags: RenameFlags,
                     ctx: RequestContext) -> None:
        ...

    async def rmdir(self, parent_inode, name: str, ctx: RequestContext) -> None:
        ...

    async def setattr(self,
                      inode: INode,
                      attr: EntryAttributes,
                      fields: SetattrFields,
                      fh: FileHandle,
                      ctx: RequestContext) -> EntryAttributes:
        ...

    async def setxattr(self, inode: INode, name: bytes, value: bytes, ctx: RequestContext) -> None:
        ...

    async def statfs(self, ctx: RequestContext) -> StatvfsData:
        ...

    async def symlink(self, parent_inode: INode, name: str, target: str, ctx: RequestContext) -> EntryAttributes:
        ...

    async def write(self, fd: FileHandle, offset: int, buf: bytes) -> int:
        ...

    async def unlink(self, parent_inode: INode, name: str, ctx: RequestContext) -> None:
        ...


__all__ = ("CharybdisOperations", )
