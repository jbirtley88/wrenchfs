import errno
import os
import sys
from fuse import FUSE, Operations, FuseOSError

class HelloFS(Operations):
    # The file that shows in the filesystem
    hello_path = '/hello'
    # The contents of that file
    hello_str = b'Hello, World!\n'

    def __init__(self, mountpoint):
        print(f'Mounting filesystem as {mountpoint} ...')
        
    def getattr(self, path, fh=None):
        if path == '/':
            # Directory attributes
            return dict(st_mode=(0o755 | 0o040000), st_nlink=2)
        elif path == self.hello_path:
            # File attributes
            return dict(st_mode=(0o444 | 0o100000), st_nlink=1, st_size=len(self.hello_str))
        else:
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        if path == '/':
            # Return directory listing
            return [
                '.',
                '..',
                self.hello_path[1:],
            ]
        else:
            raise FuseOSError(errno.ENOENT)

    def open(self, path, flags):
        if path != self.hello_path:
            raise FuseOSError(errno.ENOENT)
        # Only allow read
        allowed_flags = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & allowed_flags) != os.O_RDONLY:
            raise FuseOSError(errno.EPERM)
        return 0

    def read(self, path, size, offset, fh):
        if path != self.hello_path:
            raise FuseOSError(errno.ENOENT)
        # Simply return the contents of the file
        return self.hello_str[offset:offset + size]

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: {} <mountpoint>'.format(sys.argv[0]))
        sys.exit(1)
    mountpoint = sys.argv[1]
    FUSE(HelloFS(mountpoint), mountpoint, nothreads=True, foreground=True)
    