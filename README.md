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

## How to use CharybdisFS python client

Import all libs

    from client.client import CharybdisFsClient
    from core.faults import LatencyFault, ErrorFault, SysCall
    import errno

Connect to the rest server

    fs_client = CharybdisFsClient('127.0.0.1', 8080)

Create fault object and add it - succeeded

    latency_fault = LatencyFault(sys_call=SysCall.WRITE, probability=100, delay=1000)
    fault_id, resp = fs_client.add_fault(latency_fault)

Expected result:

    fault_id
    '3af4e469-5e36-4d6c-99a1-1919944e6419'
    resp
    <Response [200]>

Create fault object and add it - failed

    error_fault = ErrorFault(sys_call=SysCall.WRITE, probability=100, error_no=errno.EADV)
    f_id2, resp2 = fs_client.add_fault(error_fault)
    
Expected result:

    f_id2
    ''
    resp2
    <Response [500]>

Remove fault

    l = fs_client.remove_fault('3af4e469-5e36-4d6c-99a1-1919944e6419')

Expected result:

    l
    <Response [200]>
    l.text
    '{"fault_id": "3af4e469-5e36-4d6c-99a1-1919944e6419"}'
