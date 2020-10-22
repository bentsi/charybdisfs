FROM python:3.8.4-slim-buster

RUN apt update && apt install --no-install-recommends -y build-essential pkg-config libfuse3-dev curl
ADD requirements-python.txt .
RUN pip install -r requirements.txt
