FROM ubuntu:24.04

RUN apt update
RUN apt install -y fuse \
    libfuse-dev \
    git  \
    python3  \
    python3-pip  \
    python3.12-venv  \
    sudo  \
    kmod  \
    build-essential  \
    vim

RUN sed -i -e 's/^#user_allow_other/user_allow_other/' /etc/fuse.conf

RUN useradd -m -s /bin/bash wrench

# Create mount point and set permissions
# Clone the wrenchfs repo
# Create a python venv
RUN mkdir -p /mnt/fuse \
    && chown wrench /mnt/fuse 

# Switch to non-root user
USER wrench
WORKDIR /home/wrench

CMD ["/bin/bash"]

