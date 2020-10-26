FROM python:3.8.4-slim-buster

RUN apt-get update && apt-get install --no-install-recommends -y build-essential pkg-config libfuse3-dev curl
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
VOLUME /src
ENV PYTHONWARNINGS=ignore:unclosed \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/src
EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.sh"]
