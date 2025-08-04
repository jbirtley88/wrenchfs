FROM ubuntu:latest

RUN apt update
RUN apt install -y fuse libfuse-dev git python3 python3-pip python3.12-venv sudo vim

CMD ["/bin/bash"]

