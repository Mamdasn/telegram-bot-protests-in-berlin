# syntax=docker/dockerfile:1

FROM python:3.11-alpine

# Install necessary packages for building python packages
RUN apk --no-cache add gcc musl-dev libffi-dev libpq-dev

WORKDIR /app

#RUN python3 -m pip install --upgrade pip
COPY . .

RUN pip3 install -r requirements.txt

# Create a directory in the container to log the output of the code
RUN mkdir -p /app/output

