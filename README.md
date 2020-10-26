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

All CharybisFS mounts will be available inside Docker container only.

    $ docker run -it --rm --device /dev/fuse --privileged -v $(pwd):/src charybdisfs bash
    
## How to run a Docker container with mount propogation

Whole host filesystem will be available at `/docker_host_root` and if you mount CharybdisFS at any point under this directory then it'll be available on the host system too.

    $ docker run -it --rm --device /dev/fuse --privileged \
        -v $(pwd):/src -v /:/docker_host_root:rw,rshared charybdisfs bash
    

## How to run CharybdisFS for existent directory

The idea behind is to create a bind mount to have access to original files and then mount CharybdisFS to the original path.
Note that bind mounts can be done only on the same filesystem.

    $ mkdir /path/to/.shadow_source_dir
    $ mount --bind /path/to/source_dir /path/to/.shadow_source_dir
    $ python -m charybdisfs /path/to/.shadow_source_dir /path/to/source_dir

Unfortunately, you can't use this trick with Docker container mount propogation together.
