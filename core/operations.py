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

from typing import NewType, List, Tuple, Literal, Sequence

from pyfuse3 import \
    Operations, RequestContext, EntryAttributes, SetattrFields, FileInfo, StatvfsData, ReaddirToken, \
    RENAME_EXCHANGE, RENAME_NOREPLACE


INode = NewType("INode", int)
INodeList = List[Tuple[INode, int]]
FileHandle = NewType("FileHandle", int)
FileMode = NewType("FileMode", int)
RenameFlags = Literal[RENAME_EXCHANGE, RENAME_NOREPLACE]


class CharybdisOperations(Operations):
    def __init__(self, source: str):
        super().__init__()
        self.source = source

    async def access(self, inode: INode, mode: FileMode, ctx: RequestContext) -> bool:
        ...

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
        ...

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
