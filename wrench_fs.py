#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import getpass
import logging
import os

from errno import EACCES
from os.path import realpath
from threading import Lock

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

'''
This is a simple example of a FUSE filesystem that serves different content
based on a password. The filesystem has two directories:
- ./benign: Contains benign files.
- ./secret: Contains secret files.
The password 'password1' gives access to the benign files,
while 'supersecret' gives access to the secret files.

It is a basic example to demonstrate how to implement a FUSE filesystem in Python.
'''
class WrenchFS(LoggingMixIn, Operations):
    def __init__(self, password:str, mount:str):
        # Depending on the password, we serve completely different files.
        # In this (simple) example, we have two directories:
        # - ./benign: Contains benign files.
        # - ./secret: Contains secret files.
        # The password 'password1' gives access to the benign files,
        # while 'supersecret' gives access to the secret files.
        # This is a simple demonstration of how to use FUSE to create a
        # filesystem that serves different content based on a password.
        #
        # In a more complicated scenario, you might want to implement
        # more complex logic, such as checking against a database or
        # using a more secure authentication mechanism.
        #
        # Or the contents of the 'filesystem' might be a database, or
        # an encrypted blob or something.
        #
        # How you obtain the underlying files is not the important part of
        # the exercise, the important part of the exercise is to demonstrate
        # the functions that you need to implement in order to make a FUSE filesystem work
        # in python.
        if password == 'password1':
            self.root = realpath('./benign')
        elif password == 'supersecret':
            self.root = realpath('./secret')
        else:
            raise ValueError("Invalid password provided. Use 'password1' or 'supersecret'.")
        self.rwlock = Lock()
        print(f'File system mounted at: {mount}')

    def __call__(self, op, path, *args):
        return super(WrenchFS, self).__call__(op, self.root + path, *args)

    def access(self, path, mode):
        if not os.access(path, mode):
            raise FuseOSError(EACCES)

    chmod = os.chmod
    chown = os.chown

    def create(self, path, mode):
        '''
        Create a file with the given mode.
        This function is called when a file is created.
        It opens the file for writing, creating it if it does not exist,
        and truncating it to zero length if it does exist.'''
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)

    def flush(self, path, fh):
        '''
        Flush the file descriptor to disk.
        This function is called when the file is flushed.
        It ensures that all data written to the file is actually written to disk.'''
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        '''
        Synchronize the file's in-core state with storage.
        This function is called to ensure that all data written to the file
        is actually written to disk. The `datasync` parameter indicates whether
        to synchronize data only or both data and metadata.
        If `datasync` is non-zero, it performs a data-only sync; otherwise,
        it performs a full sync including metadata.
        '''
        if datasync != 0:
            return os.fdatasync(fh)
        else:
            return os.fsync(fh)

    def getattr(self, path, fh=None):
        '''
        Get the attributes of a file or directory.
        This function retrieves the attributes of a file or directory,
        such as its size, permissions, and timestamps.
        It uses `os.lstat` to get the attributes without following symbolic links.
        The attributes are returned as a dictionary with keys like 'st_size',
        'st_mode', 'st_uid', 'st_gid', 'st_atime', 'st_mtime', 'st_ctime', and 'st_nlink'.
        If `fh` is provided, it retrieves the attributes of the file
        associated with the file descriptor; otherwise,
        it retrieves the attributes of the file specified by `path`.
        If the file does not exist, it raises a `FuseOSError` with the error code `ENOENT`.
        If the file is a directory, it returns the attributes of the directory
        instead of the file.
        If the file is a symbolic link, it returns the attributes of the link itself.
        If the file is a special file (like a socket or a pipe), it returns the
        attributes of the special file.
        If the file is a block device or a character device, it returns the attributes
        of the device.
        '''
        st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
            'st_nlink', 'st_size', 'st_uid'))

    getxattr = None

    def link(self, target, source):
        '''
        Create a hard link to a file.
        This function creates a hard link from `source` to `target`.
        A hard link is a directory entry that associates a name with a file on the filesystem.
        It allows multiple names to refer to the same file content.
        The `source` parameter is the path to the existing file,
        and the `target` parameter is the path where the hard link will be created.
        '''
        return os.link(self.root + source, target)

    # Because we don't support extended attributes, we set these to None.
    listxattr = None
    
    # Because the functions we override have exactly the same signature as the
    # original functions, we can just use the original functions directly.
    mkdir = os.mkdir
    mknod = os.mknod
    open = os.open
    readlink = os.readlink
    rmdir = os.rmdir
    unlink = os.unlink
    utimens = os.utime
    
    def rename(self, old, new):
        '''
        Rename a file or directory.
        This function renames the file or directory specified by `old` to `new`.
        The `old` parameter is the current name of the file or directory,
        and the `new` parameter is the new name to which it will be renamed.
        If the `new` name already exists, it will be overwritten.
        '''
        return os.rename(old, new)
    
    def read(self, path, size, offset, fh):
        '''
        Read data from a file.
        This function reads `size` bytes of data from the file specified by `path`
        starting at the given `offset`. It uses the file descriptor `fh` to read
        the data from the file.
        The `fh` parameter is the file descriptor obtained from the `open` function.
        '''
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        '''
        Read the contents of a directory.
        This function reads the contents of the directory specified by `path`.
        It returns a list of names of the files and directories in the directory.
        The `fh` parameter is the file descriptor of the directory (if the directory was 
        opened with opendir().
        
        Because this is a filesystem, we prepend the special entries '.' and '..'
        '''
        return ['.', '..'] + os.listdir(path)


    def release(self, path, fh):
        '''Release a file descriptor.
        This function is called when a file is closed.
        It releases the file descriptor `fh` associated with the file specified by `path`.
        The `fh` parameter is the file descriptor obtained from the `open` function.
        '''
        return os.close(fh)

    def statfs(self, path):
        '''
        Get the details of a file using stat()
        '''
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail',
            'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'))

    def symlink(self, target, source):
        '''Create a symbolic link.
        This function creates a symbolic link from `source` to `target`.
        '''
        return os.symlink(source, target)

    def truncate(self, path, length, fh=None):
        '''
        Truncate a file to a specified length.
        This function truncates the file specified by `path` to the given `length`.
        If `fh` is provided, it uses the file descriptor to truncate the file.
        If `fh` is not provided, it opens the file in read/write mode and truncates it.
        If the file is larger than `length`, it will be reduced to the specified size.
        If the file is smaller than `length`, it will be extended with null bytes.
        '''
        with open(path, 'r+') as f:
            f.truncate(length)


    def write(self, path, data, offset, fh):
        '''
        Write data to a file.
        This function writes the `data` to the file specified by `path`
        starting at the given `offset`. It uses the file descriptor `fh` to write
        the data to the file.
        The `data` parameter is a bytes object containing the data to be written.
        The `offset` parameter specifies the position in the file where the data should be written.
        The `fh` parameter is the file descriptor obtained from the `open` function.
        If the file does not exist, it raises a `FuseOSError` with the error code `ENOENT`.
        If the file is not opened for writing, it raises a `FuseOSError` with the error code `EACCES`.
        If the file is a directory, it raises a `FuseOSError` with the error code `EISDIR`.
        If the file is a symbolic link, it raises a `FuseOSError` with the error code `ELOOP`.
        If the file is a special file (like a socket or a pipe), it raises a `FuseOSError` with the error code `ENOTSUP`.
        '''
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.write(fh, data)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    args = parser.parse_args()

    password = getpass.getpass("Enter password: ")
    # Set thie to 'DEBUG' for the gory details
    logging.basicConfig(level=logging.INFO)
    fuse = FUSE(
        WrenchFS(password), args.mount, foreground=True, allow_other=True)
