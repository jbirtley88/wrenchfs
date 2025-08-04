# WrenchFS
A minimal FUSE filesystem in Python

It is inspired by this https://xkcd.com/538/: 

![Wrench](./xkcd-wrench.png)

To get the *harmless* files, the password is `password1`.

To access the *secret* files, the password is `supersecret`.

The idea being that, when being hit with the wrench, you can hand over a password that works whilst keeping your supersecret files super secret.

# Step 1: Installing FUSE
## Linux
Installing on Linux is a little more straightforward:
```sh
    $ sudo apt update
    $ sudo apt install fuse libfuse-dev
```

(Docker is a **TODO**, mainly because you can't install kernel modules into docker containers so it needs to be installed on the host)

# Step 2: Configuring FUSE
Make sure that FUSE is configured correctly, by uncommenting the `user_allow_other` in `/etc/fuse.conf`:
```sh
    ubuntu$ sudo sed -i -e 's/^#user_allow_other/user_allow_other/' /etc/fuse.conf
```

# Step 3: Clone The `wrenchfs` Repo
Clone the `wrenchfs` repo:
```sh
    ubuntu:/var/tmp/wrenchfs$ cd /var/tmp
    ubuntu:/var/tmp/wrenchfs$ git clone https://github.com/jbirtley88/wrenchfs.git
    ubuntu:/var/tmp/wrenchfs$ cd wrenchfs
    ubuntu:/var/tmp/wrenchfs$ git remote -v
    origin	https://github.com/jbirtley88/wrenchfs.git (fetch)
    origin	https://github.com/jbirtley88/wrenchfs.git (push)
```
Finally, you'll want to create a python virtual env and install the `fusepy` package:
```sh
    ubuntu:/var/tmp/wrenchfs$ python3 -m venv .venv
    $ source .venv/bin/activate

    (.venv) ubuntu:/var/tmp/wrenchfs$ pip3 install -r requirements.txt
$ pip3 install -r requirements.txt 
    Collecting fusepy (from -r requirements.txt (line 1))
    ...
    Installing collected packages: fusepy
    Successfully installed fusepy-3.0.1
```
You're now ready to run your first filesystem and, like all great engineering tutorials, this will be a *Hello, World!*.

First, though, just take a moment to get your head round what we're actually doing when we run FUSE:

# FUSE From 10,000 Feet
```
+-------+      +-----+     +------+      +--------------+    +-------------------+     
| ls -l |      | VFS |     | FUSE |      |  your_fs.py  |    |  YourFS.statfs()  |
+---+---+      +--+--+     +---+--+      +-------+------+    +----------+--------+
    |             |            |                 |                      |
    +------------>+            |                 |                      |
    |             +----------->+                 |                      |
    |                          +---------------->+                      |
    |                                            +--------------------->+ Your implementation in code
    |                                                                   |
    |                                            +<---------------------+
    |                          <-----------------+   list_of_files['.', '..', 'hello.txt'. ]
    |             +<-----------+
    +<------------+
```
Your `ls -l` goes through the kernel VFS in the normal way - mapping the underlying `stat(2)` system call to the appropriate kernel handler.  This happens regardless of where the filesystem lives or on what device it is located.

In our case, the kernel handler is `FUSE` (*Filesystem in USer spacE*).

`FUSE` then, via `your_fs.py`, invokes the `statfs()` function in your code.

You are now on the end of a `stat(2)` request, and the `ls -l` command is waiting on your code to return the result.

Let that sink in - it is **your code** that is responsible for generating the response - FUSE is doing all the heavy lifting of getting the request to your code, whilst presenting (what looks like and is) a filesystem to the user.

Your code can do whatever it likes to generate the request - you have the entire Python universe at your disposal.  Anything you can do in python, you can do here:

- read from a database
- read from a HTTP endpoint
- dig inside a .zip / .tar file
- decrypt an encrypted blob
- say 'hello world'

Let's look a three examples - the last of this is `WrenchFS` (our supersecret filesystem).

# FUSE Basics 1: `HelloFS`
Our first example is in [hello_fs.py](hello_fs.py) - the most most simple and basic FUSE filesystem which only knows how to say *'Hello, World!'* via a file called `hello`.  

First, mount the FUSE filesystem:
```sh
    # Make sure that the filesystem is not already mounted
    $ umount /var/tmp/hellofs

    # Make sure the mount point exists
    $ mkdir -p /var/tmp/hellofs 2>/dev/null

    # Mount our filesystem
    $ python3 hello_fs.py /var/tmp/hellofs
    Mounting filesystem as /var/tmp/hellofs ...
```
Now `/var/tmp/hellofs` is a mounted filesystem, just like `/` or any other filesystem:
```sh
    $ mount | grep /var/tmp/hello
    HelloFS on /var/tmp/hellofs type fuse (rw,nosuid,nodev,relatime,user_id=1000,group_id=1000)
```
To anything running in userspace (ie anything that is not the OS), `var/tmp/hellofs` is a mounted filesystem that you interact with exactly the same as you'd interact with any filesystem:
```sh
    $ ls -ld /var/tmp/hellofs
    drwxr-xr-x 2 root root 0 Jan  1  1970 /var/tmp/hellofs

    $ ls -l /var/tmp/hellofs/.
    total 0
    -r--r--r-- 1 root root 14 Jan  1  1970 hello.    # provided by HelloFS.getattr()

    $ cat /var/tmp/hellofs/hello
    Hello, World!
```

## How It Works
For this simple example, we only need to implement four functions:

- `def getattr(self, path, fh=None):`
  Get the attributes (i.e. the details shown in `ls -l`).
  We specifically check for the `'/hello'` path in code

- `def readdir(self, path, fh):`
  Read (list) the contents of a directory (e.g. when using `ls -l`)
  Just like it's `readdir(3)` counterpart.
  We specifically check for the `'/hello'` path in code

- `def open(self, path, flags):`
  Open a file (for reading / writing - according to the `flags`: `O_RDONLY`, `O_WRONLY` etc),
  just like its `open(2)` counterpart
  Again, we specifically check for the `'/hello'` path in code

- `def read(self, path, size, offset, fh):`
  Read a file, just like its `read(2)` counterpart
  Again, we specifically check for the `'/hello'` path in code

That's all it takes to implement a filesystem in python.


# FUSE Basics 2: `FormatFS`
(See [format_fs.py](format_fs.py))
This is prettymuch the same as `HelloFS` in that it only implements the same four functions, and presents a single file called `hello`.

What makes it different is that we can - using only the filesystem and the `cat(1)` command, get the contents of `hello` in a variety of formats:
```sh
    $ ls -l /var/tmp/formatfs/.
    total 0
    -r--r--r-- 1 root root 14 Jan  1  1970 hello

    $ cat /var/tmp/formatfs/hello
    Hello, World!
```

- text (default)
```sh
    # Note the .txt extension
    $ cat /var/tmp/formatfs/hello.txt
    Hello, World!
    # But no /var/tmp/formats/hello.txt ... wait, wut?
    $ ls -l /var/tmp/formatfs/.
    total 0
    -r--r--r-- 1 root root 14 Jan  1  1970 hello
```

- csv
```sh
    # Note the .csv extension
    $ cat /var/tmp/formatfs/hello.csv
    # But no /var/tmp/formats/hello.csv ... wait, wut?
    $ ls -l /var/tmp/formatfs/.
    total 0
    -r--r--r-- 1 root root 14 Jan  1  1970 hello
```

- json
```sh
    # Note the .json extension
    $ cat /var/tmp/formatfs/hello.json
    # But no /var/tmp/formats/hello.json ... wait, wut?
    $ ls -l /var/tmp/formatfs/.
    total 0
    -r--r--r-- 1 root root 14 Jan  1  1970 hello
```

- xml
```sh
    # Note the .xml extension
    $ cat /var/tmp/formatfs/hello.xml
    # But no /var/tmp/formats/hello.xml ... wait, wut?
    $ ls -l /var/tmp/formatfs/.
    total 0
    -r--r--r-- 1 root root 14 Jan  1  1970 hello
```

First, mount the FUSE filesystem:
```sh
    # Make sure that the filesystem is not already mounted
    $ umount /var/tmp/formatfs

    # Make sure the mount point exists
    $ mkdir -p /var/tmp/formatfs 2>/dev/null

    # Mount our filesystem
    $ python3 format_fs.py /var/tmp/formatfs
    Mounting filesystem as /var/tmp/formatfs ...
```
Again, `/var/tmp/formatfs` is a mounted filesystem, just like `/` or any other filesystem

Why is that useful?

It's useful because it makes any client code (or anything accessing the contents of the file full-stop) significantly easier.

For instance, how could you do any of these on a command-line?

- `cat hello.json | convert-json-to-csv > hello.csv`

- `cat hello.xml | convert-xml-to-text > hello.txt`

Not impossible, but not immediately straightforward.

By delegating the *what-format-do-I-want-this-in* to the filesystem itself, your code (and your scripts) can become significantly quicker to develop and significantly easier to maintain.

## How It Works
The key moving part of `FormatFS` (and the key difference from `HelloFS` happens) in the `read()` method:
```python
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

    def read(self, path, size, offset, fh):
        if path == self.hello_path:
            # No extension, return the default format
            return self.content_by_format[self.default_format]
        if len(path) > 7 and path[0:len(self.hello_path + '.')] == self.hello_path + '.':
            # Check if the path has a recognised extension
            ext = path[len(self.hello_path + '.'):]
            if ext not in self.content_by_format:
                raise FuseOSError(errno.ENOENT)
            # Return the content for the requested format
            return self.content_by_format[ext]
        raise FuseOSError(errno.ENOENT)
```

# Finally, The WrenchFS Filesystem
(See [wrench_fs.py](wrench_fs.py))
`WrenchFS`ß is a filesystem which serves two completely different sets of files, depending on which password you give it when mounting the filesystem.

It is particularly useful when you're been beaten with a $5 wrench in order to give up the password to unlock your files.

In this example, the underlying files are stored in the `benign` and `secret` directories respectively.

All of the fun happens in the `WrenchFS` constructor:
```py
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
```
Basically, we just set `self.root` depending on which password was used.

The rest of the class simply delegates all operations to the underlying real directory on disk (known as a *passthrough* implementation in FUSE) by prepending the `self.root`:
```py
    # Wrap calls to the original functions with our self.root prepended
    def __call__(self, op, path, *args):
        return super(WrenchFS, self).__call__(op, self.root + path, *args)
        
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
```

# Conclusion
When you consider (and truly internalise) that FUSE allows your client code to interact with a real filesystem - and that filesystem is nothing more than python code - you can hopefully start to see how powerful it is:

- mount a SQL database as a filesystem
- mount a NoSQL database as a filesystem
- mount .zip or .tar files as a filesystem
- mount an email account as a filesystem

