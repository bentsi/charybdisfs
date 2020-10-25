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
import stat
import errno
from typing import NewType, List, Tuple, Literal, Sequence, Dict, Optional, Union, Set, NoReturn, cast
from functools import wraps
from collections import Counter

import pyfuse3
from pyfuse3 import \
    Operations, RequestContext, EntryAttributes, SetattrFields, FileInfo, StatvfsData, ReaddirToken, FUSEError, \
    RENAME_EXCHANGE, RENAME_NOREPLACE, ROOT_INODE


# Everything from manpage statvfs(2) except f_flag and f_sid.
STATVFS_DATA_FIELDS = \
    ("f_bsize", "f_frsize", "f_blocks", "f_bfree", "f_bavail", "f_files", "f_ffree", "f_favail", "f_namemax", )


INode = NewType("INode", int)
INodeList = List[Tuple[INode, int]]
FileDescriptor = NewType("FileDescriptor", int)
FileHandle = NewType("FileHandle", int)
FileMode = NewType("FileMode", int)
RenameFlags = Literal[RENAME_EXCHANGE, RENAME_NOREPLACE]


class PathMapping(Dict[INode, Union[str, Set[str]]]):
    def __init__(self, root):
        super().__init__({ROOT_INODE: root, })
        self.inode_lookups: Counter = Counter()
        self.path_prefix_len = len(root) + 1

    def __getitem__(self, inode: INode) -> str:
        path = super().__getitem__(inode)
        if isinstance(path, set):
            for path in path:
                break
        return path

    def __setitem__(self, inode: INode, path: str) -> None:
        self.inode_lookups[inode] += 1
        if (old_path := super().get(inode)) is not None:
            if isinstance(old_path, set):
                old_path.add(path)
            elif old_path != path:
                super().__setitem__(inode, {old_path, path})
        else:
            super().__setitem__(inode, path)

    def forget_path(self, inode: INode, path: str) -> None:
        if (inode_path := super().get(inode)) is None:
            return
        if isinstance(inode_path, set):
            inode_path.remove(path)  # can raise KeyError if there is no such path
            if len(inode_path) == 1:
                for path in inode_path:
                    super().__setitem__(inode, path)
        elif inode_path == path:
            del self[inode]
        else:
            raise KeyError(path)

    def replace_path(self, inode: INode, old_path: str, new_path: str) -> None:
        if (path := super().get(inode)) is None:
            return
        if isinstance(path, set):
            path.remove(old_path)  # can raise KeyError if there is no such path
            path.add(new_path)
        else:
            if path != old_path:
                raise KeyError(old_path)
            super().__setitem__(inode, new_path)

    def forget_inode_lookups(self, inode: INode, nlookup: int) -> bool:
        """Return True if inode removed from the mapping."""

        if nlookup >= self.inode_lookups[inode]:
            del self.inode_lookups[inode]
            self.pop(inode, None)
            return True
        self.inode_lookups[inode] -= nlookup
        return False


class FileDescriptorMapping(Dict[INode, FileDescriptor]):
    def __init__(self):
        super().__init__()
        self.inodes: Dict[FileDescriptor, INode] = {}
        self.open_counters = Counter()

    def __setitem__(self, inode: INode, fd: FileDescriptor):
        if inode in self:
            raise ValueError("Can't assign same inode twice")
        super().__setitem__(inode, fd)
        self.inodes[fd] = inode
        self.open_counters[fd] = 1

    def __delitem__(self, inode: INode):
        del self.inodes[(fd := super().pop(inode))]
        del self.open_counters[fd]

    def acquire_by_inode(self, inode: INode) -> Optional[FileDescriptor]:
        if (fd := self.get(inode)) is not None:
            self.open_counters[fd] += 1
        return fd

    def acquire(self, fd: FileDescriptor) -> None:
        self.open_counters[fd] += 1

    def release(self, fd: FileDescriptor) -> bool:
        """Return True if associated inode removed from the mapping."""

        if self.open_counters[fd] == 1:
            del self[self.inodes[fd]]
            return True
        self.open_counters[fd] -= 1
        return False


class CharybdisRuntimeErrors:
    @staticmethod
    def try_to_replace_fd_for_inode(inode: INode,
                                    old_fd: FileDescriptor,
                                    new_fd: FileDescriptor,
                                    exc: Optional[Exception] = None) -> NoReturn:
        raise RuntimeError(f"Try to replace {old_fd=} with {new_fd=} for {inode=}") from None

    @staticmethod
    def forgot_inode_with_open_fd(inode: INode, fd: FileDescriptor, exc: Optional[Exception] = None) -> NoReturn:
        raise RuntimeError(f"Forgot about {inode=} with open {fd=}") from None

    @staticmethod
    def unknown_path(inode: INode, path: str, exc: Optional[Exception] = None) -> NoReturn:
        raise RuntimeError(f"Unknown {path=} for {inode=}") from None

    @staticmethod
    def unknown_fd(fd: FileDescriptor, exc: Optional[Exception] = None) -> NoReturn:
        raise RuntimeError(f"Unknown {fd=}") from None


class faulty:
    """Descriptor for methods which faults can be applied.

    Methods shouldn't be static or class methods.
    """

    # TODO: make it works with static and class methods.

    def __init__(self, func):
        self.__func__ = func

    def __get__(self, instance, owner=None):
        @wraps(self.__func__)
        def wrapper(*args, **kwargs):
            # TODO: we can add inserting faults machinery right here.
            return self.__func__(instance, *args, **kwargs)
        return wrapper

    def __set_name__(self, owner, name):
        if not hasattr(owner, "faulty_methods"):
            owner.faulty_methods = set()
        owner.faulty_methods.add(name)


class CharybdisOperations(Operations):
    enable_writeback_cache = True
    runtime_errors = CharybdisRuntimeErrors()

    def __init__(self, source: str):
        super().__init__()
        self.paths = PathMapping(root=source.rstrip("/"))
        self.descriptors = FileDescriptorMapping()

    @faulty
    async def access(self, inode: INode, mode: FileMode, ctx: RequestContext) -> bool:
        return os.access(self.paths[inode], mode=mode)

    @faulty
    async def create(self,
                     parent_inode: INode,
                     name: str,
                     mode: FileMode,
                     flags: int,
                     ctx: RequestContext) -> Tuple[FileInfo, EntryAttributes]:
        path = os.path.join(self.paths[parent_inode], os.fsdecode(name))
        try:
            fd = os.open(path, flags | os.O_CREAT | os.O_TRUNC)
        except OSError as exc:
            raise FUSEError(exc.errno)
        attrs = self._get_attr(fd)
        inode = attrs.st_ino
        self.paths[inode] = path
        self.descriptors[inode] = fd
        return FileInfo(fh=fd), attrs

    @faulty
    async def forget(self, inode_list: INodeList) -> None:
        for inode, nlookup in inode_list:
            if self.paths.forget_inode_lookups(inode=inode, nlookup=nlookup) and inode in self.descriptors:
                self.runtime_errors.forgot_inode_with_open_fd(inode=inode, fd=self.descriptors[inode])

    @faulty
    async def flush(self, fh: FileHandle) -> None:
        fd = cast(FileDescriptor, fh)
        if fd not in self.descriptors.inodes:
            self.runtime_errors.unknown_fd(fd=fd)
        try:
            open(file=fd, mode="r+b", closefd=False).flush()  # not sure about which mode we should use here.
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def fsync(self, fh: FileHandle, datasync: bool) -> None:
        try:
            if datasync:
                os.fdatasync(fh)
            else:
                os.fsync(fh)
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def fsyncdir(self, fh: FileHandle, datasync: bool) -> None:
        return await self.fsync(fh=fh, datasync=datasync)

    @staticmethod
    def _get_attr(target: Union[str, FileDescriptor]) -> EntryAttributes:
        try:
            stat_result = os.stat(target, follow_symlinks=False)
        except OSError as exc:
            raise FUSEError(exc.errno)

        stat_attrs = [attr for attr in dir(stat_result) if attr.startswith("st_")]
        entry_attrs = EntryAttributes()
        for stat_attr in stat_attrs:
            if getattr(entry_attrs, stat_attr):
                setattr(entry_attrs, stat_attr, getattr(stat_result, stat_attr))
        entry_attrs.attr_timeout = 0
        entry_attrs.entry_timeout = 0
        return entry_attrs

    @faulty
    async def getattr(self, inode: INode, ctx: RequestContext) -> EntryAttributes:
        if (target := self.descriptors.get(inode)) is None:
            target = self.paths[inode]
        return self._get_attr(target)

    @faulty
    async def getxattr(self, inode: INode, name: bytes, ctx: RequestContext) -> bytes:
        try:
            return pyfuse3.getxattr(path=self.paths[inode], name=_bytes2str(name))
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def link(self,
                   inode: INode,
                   new_parent_inode: INode,
                   new_name: bytes,
                   ctx: RequestContext) -> EntryAttributes:
        new_path = os.path.join(self.paths[new_parent_inode], os.fsdecode(new_name))
        try:
            os.link(src=self.paths[inode], dst=new_path, follow_symlinks=False)
        except OSError as exc:
            raise FUSEError(exc.errno) from None
        self.paths[inode] = new_path
        return await self.getattr(inode=inode, ctx=ctx)

    @faulty
    async def listxattr(self, inode: INode, ctx: RequestContext) -> Sequence[bytes]:
        try:
            return [_str2bytes(attr) for attr in os.listxattr(path=self.paths[inode], follow_symlinks=False)]
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def lookup(self, parent_inode: INode, name: str, ctx: RequestContext) -> INode:
        path = os.path.join(self.paths[parent_inode], os.fsdecode(name))
        attr = self._get_attr(path)
        if name not in (".", ".."):
            self.paths[attr.st_ino] = path
        return attr

    @faulty
    async def mkdir(self, parent_inode: INode, name: str, mode: FileMode, ctx: RequestContext) -> EntryAttributes:
        ...

    @faulty
    async def mknod(self,
                    parent_inode: INode,
                    name: str,
                    mode: FileMode,
                    rdev: int,
                    ctx: RequestContext) -> EntryAttributes:
        path = os.path.join(self.paths(parent_inode), os.fsdecode(name))
        try:
            os.mknod(path=path, mode=(mode & ~ctx.umask), device=rdev)
            os.chown(path=path, uid=ctx.uid, gid=ctx.gid)
        except OSError as exc:
            raise FUSEError(exc.errno)
        attr = self._getattr(path)
        self.paths[attr.st_ino] = path
        return attr

    @faulty
    async def open(self, inode: INode, flags: int, ctx: RequestContext) -> FileInfo:
        if (fd := self.descriptors.acquire_by_inode(inode)) is None:
            if flags & os.O_CREAT:
                raise FUSEError(errno.EINVAL)
            try:
                fd = cast(FileDescriptor, os.open(self.paths[inode], flags))
            except OSError as exc:
                raise FUSEError(exc.errno) from None
            try:
                self.descriptors[inode] = fd
            except ValueError:
                self.runtime_errors.try_to_replace_fd_for_inode(inode=inode, old_fd=self.descriptors[inode], new_fd=fd)
        return FileInfo(fh=fd)

    @faulty
    async def opendir(self, inode: INode, ctx: RequestContext) -> FileHandle:
        return cast(FileHandle, inode)

    @faulty
    async def read(self, fh: FileHandle, off: int, size: int) -> bytes:
        try:
            os.lseek(fh, off, os.SEEK_SET)
            return os.read(fh, size)
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def readdir(self, inode: INode, start_id: int, token: ReaddirToken) -> None:
        ...

    @faulty
    async def readlink(self, inode: INode, ctx: RequestContext) -> bytes:
        try:
            return os.fsencode(os.readlink(self.paths[inode]))
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def release(self, fh: FileHandle) -> None:
        if self.descriptors.release(cast(FileDescriptor, fh)):
            try:
                os.close(fh)
            except OSError as exc:
                raise FUSEError(exc.errno)

    @faulty
    async def releasdir(self, fh: FileHandle) -> None:
        ...

    @faulty
    async def removexattr(self, inode: INode, name: bytes, ctx: RequestContext) -> None:
        try:
            os.removexattr(path=self.paths[inode], attribute=name, follow_symlinks=False)
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def rename(self,
                     parent_inode_old: INode,
                     name_old: bytes,
                     parent_inode_new: INode,
                     name_new: bytes,
                     flags: RenameFlags,
                     ctx: RequestContext) -> None:
        if flags:
            raise FUSEError(errno.EINVAL)

        old_path = os.path.join(self.paths[parent_inode_old], os.fsdecode(name_old))
        new_path = os.path.join(self.paths[parent_inode_new], os.fsdecode(name_new))
        try:
            os.rename(src=old_path, dst=new_path)
            inode = cast(INode, os.lstat(new_path).st_ino)
        except OSError as exc:
            raise FUSEError(exc.errno)

        try:
            self.paths.replace_path(inode=inode, old_path=old_path, new_path=new_path)
        except KeyError:
            self.runtime_errors.unknown_path(inode=inode, path=old_path)

    @faulty
    async def rmdir(self, parent_inode, name: bytes, ctx: RequestContext) -> None:
        path = os.path.join(self.paths[parent_inode], os.fsdecode(name))
        try:
            inode = cast(INode, os.lstat(path).st_ino)
            os.rmdir(path)
        except OSError as exc:
            raise FUSEError(exc.errno) from None
        try:
            self.paths.forget_path(inode=inode, path=path)
        except KeyError:
            self.runtime_errors.unknown_path(inode=inode, path=path)

    @faulty
    async def setattr(self,
                      inode: INode,
                      attr: EntryAttributes,
                      fields: SetattrFields,
                      fh: FileHandle,
                      ctx: RequestContext) -> EntryAttributes:
        target = self.paths[inode] if fh is None else fh
        try:
            if fields.update_size:
                os.truncate(path=target, length=attr.st_size)

            if fields.update_mode:
                if stat.S_ISLNK(attr.st_mode):
                    # setattr call will never happen on symlinks under Linux.
                    raise FUSEError(errno.EINVAL)
                os.chmod(path=target, mode=stat.S_IMODE(attr.st_mode))

            uid = gid = -1
            if fields.update_uid:
                uid = attr.st_uid
            if fields.update_gid:
                gid = attr.st_gid
            if uid != -1 or gid != -1:
                os.chown(path=target, uid=uid, gid=gid, follow_symlinks=False)

            atime_ns = mtime_ns = None
            if fields.update_atime != fields.update_mtime:
                old_attr = os.stat(path=target)
                atime_ns = old_attr.st_atime_ns
                mtime_ns = old_attr.st_mtime_ns
            if fields.update_atime:
                atime_ns = attr.st_atime_ns
            if fields.update_mtime:
                mtime_ns = attr.st_mtime_ns
            if atime_ns is not None:  # at this point both atime_ns and mtime_ns are set or not set simultaneously.
                os.utime(path=target, ns=(atime_ns, mtime_ns), follow_symlinks=fh is not None)
        except OSError as exc:
            raise FUSEError(exc.errno) from None
        return await self.getattr(inode=inode, ctx=ctx)

    @faulty
    async def setxattr(self, inode: INode, name: bytes, value: bytes, ctx: RequestContext) -> None:
        try:
            pyfuse3.setxattr(path=self.paths[inode], name=_bytes2str(name), value=value)
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def statfs(self, ctx: RequestContext) -> StatvfsData:
        try:
            statvfs_result = os.statvfs(self.paths[ROOT_INODE])
        except OSError as exc:
            raise FUSEError(exc.errno) from None
        statvfs_data = StatvfsData()
        for field in STATVFS_DATA_FIELDS:
            setattr(statvfs_data, field, getattr(statvfs_result, field))
        statvfs_data.f_namemax -= self.paths.path_prefix_len
        return statvfs_data

    @faulty
    async def symlink(self, parent_inode: INode, name: bytes, target: bytes, ctx: RequestContext) -> EntryAttributes:
        path = os.path.join(self.paths[parent_inode], os.fsdecode(name))
        try:
            os.symlink(src=os.fsdecode(target), dst=path)
            os.chown(path=path, uid=ctx.uid, gid=ctx.gid, follow_symlinks=False)
        except OSError as exc:
            raise FUSEError(exc.errno) from None
        symlink_inode = cast(INode, os.lstat(path).st_ino)
        self.paths[symlink_inode] = path
        return await self.getattr(inode=symlink_inode, ctx=ctx)

    @faulty
    async def write(self, fh: FileHandle, off: int, buf: bytes) -> int:
        try:
            os.lseek(fh, off, os.SEEK_SET)
            return os.write(fh, buf)
        except OSError as exc:
            raise FUSEError(exc.errno) from None

    @faulty
    async def unlink(self, parent_inode: INode, name: bytes, ctx: RequestContext) -> None:
        path = os.path.join(self.paths[parent_inode], os.fsdecode(name))
        try:
            inode = cast(INode, os.lstat(path).st_ino)
            os.unlink(path)
        except OSError as exc:
            raise FUSEError(exc.errno) from None
        try:
            self.paths.forget_path(inode=inode, path=path)
        except KeyError:
            self.runtime_errors.unknown_path(inode=inode, path=path)


def _str2bytes(val: str, /) -> bytes:
    return val.encode(encoding=pyfuse3.fse, errors="surrogateescape")


def _bytes2str(val: bytes, /) -> str:
    return val.decode(encoding=pyfuse3.fse, errors="surrogateescape")


__all__ = ("CharybdisOperations", )
