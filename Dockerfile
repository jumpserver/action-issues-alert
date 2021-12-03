# Container image that runs your code
FROM python:3.8-alpine

# Copies your code file from your action repository to the filesystem path `/` of the container
RUN apk --update add --no-cache bash gcc make libc-dev libffi-dev
COPY *.py *.sh requirements.txt /
RUN pip install -r /requirements.txt

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]
