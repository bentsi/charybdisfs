# CharybdisFS

A remotely controlled fault injection file system.

##  Create virtualenv using PyEnv
    $ pyenv virtualenv 3.8.4 charybdisfs

##  Install pre-requisites

### Ubuntu 20.04
    $ sudo apt install build-essential pkg-config libfuse3-dev

###  CentOS 7
    $ sudo yum install fuse3 fuse3-devel

##  Install Python requirements
    $ pyenv local charybdisfs
    $ pip install -r requirements.txt

##  How to run a Docker container
    $ docker build -t charybdisfs .
    $ docker run -it --device /dev/fuse --privileged -v /:/system_root charybdisfs /bin/bash
