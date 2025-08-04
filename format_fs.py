import errno
import os
import sys
from fuse import FUSE, Operations, FuseOSError

class FormatFS(Operations):
    # The base filename that shows in the filesystem
    hello_path = '/hello'
    
    # The formats that we support.
    #
    # By appending one of these extensions to the base filename, we can
    # create different representations of the same content.
    content_by_format = {
        'csv': b'greeting,recipient\nHello,World!\n',
        'txt': b'Hello, World!\n',
        'json': b'{"message": "Hello, World!"}\n',
        'xml': b'<message>Hello, World!</message>\n',
    }
    
    # The default output is text
    default_format = 'txt'

    def __init__(self, mountpoint):
        print(f'Mounting filesystem as {mountpoint} ...')
        
    def getattr(self, path, fh=None):
        if path == '/':
            # Directory attributes
            return dict(st_mode=(0o755 | 0o040000), st_nlink=2)
        if path == self.hello_path:
            return dict(st_mode=(0o444 | 0o100000), st_nlink=1, st_size=len(self.content_by_format[self.default_format]))        
        if len(path) > 7 and path[0:len(self.hello_path + '.')] == self.hello_path + '.':
            # File attributes
            for ext in self.content_by_format:
                if path == f'{self.hello_path}.{ext}':
                    # This is a supported format (file extension)
                    return dict(st_mode=(0o444 | 0o100000), st_nlink=1, st_size=len(self.content_by_format[ext]))
        # If we get to here, then we either have an unsupported format or a file that doesn't exist
        raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        if path == '/':
            # Return directory listing
            return [
                '.',
                '..',
                
                # We only show the file listing as 'hello'.
                # We don't show the extensions in the directory listing.
                # This is to reinforce the idea that - beyond the basic plumbing -
                # the filesystem is 100% a software construct.
                # That mental leap - "this filesystem is 100% software" - is the
                # key to understanding how this works and is often the most difficult
                # mental leap to make
                self.hello_path[1:],
            ]
        else:
            raise FileNotFoundError

    def open(self, path, flags):
        if path != self.hello_path:
            raise FileNotFoundError
        # Only allow read
        allowed_flags = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & allowed_flags) != os.O_RDONLY:
            raise PermissionError
        return 0

    def read(self, path, size, offset, fh):
        if path == self.hello_path:
            # No extension, return the default format
            return self.content_by_format[self.default_format]
        if len(path) > 7 and path[0:len(self.hello_path + '.')] == self.hello_path + '.':
            # Check if the path has a valid extension
            ext = path[len(self.hello_path + '.'):]
            if ext not in self.content_by_format:
                raise FuseOSError(errno.ENOENT)
            # Return the content for the requested format
            return self.content_by_format[ext]
        raise FuseOSError(errno.ENOENT)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: {} <mountpoint>'.format(sys.argv[0]))
        sys.exit(1)
    mountpoint = sys.argv[1]
    FUSE(FormatFS(mountpoint), mountpoint, nothreads=True, foreground=True)
    