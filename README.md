# CharybdisFS

A remotely controlled fault injection file system.

## Create virtualenv using PyEnv
    $ pyenv virtualenv 3.8.4 charybdisfs

## Install pre-requisites

### Ubuntu 20.04
    $ sudo apt install build-essential pkg-config libfuse3-dev

### CentOS 7
    $ sudo yum install fuse3 fuse3-devel

## Install Python requirements
    $ pyenv local charybdisfs
    $ pip install -r requirements.txt

## How to build a Docker image
    $ docker build -t charybdisfs .
    
##  How to run a Docker container
    $ docker run -it --device /dev/fuse --privileged /bin/bash
    
## How to run a Docker container with mount propogation
    $ docker run -it --device /dev/fuse --privileged \
        --mount type=bind,source=/,target=/docker_host_root,bind-propagation=rshared charybdisfs /bin/bash

## How to run CharybdisFS for existent directory

The idea behind is to create a bind mount to have access to original files and then mount CharybdisFS to the original path.
Note that bind mounts can be done only on the same filesystem.

    $ mkdir /path/to/.shadow_source_dir
    $ mount --bind /path/to/source_dir /path/to/.shadow_source_dir
    $ python -m charybdisfs /path/to/.shadow_source_dir /path/to/source_dir
