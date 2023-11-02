# syntax=docker/dockerfile:1

FROM python:3.11-alpine

WORKDIR /app

#RUN python3 -m pip install --upgrade pip
COPY requirements.txt requirements-postgresupdater.txt
RUN pip3 install -r requirements-postgresupdater.txt

COPY . .

CMD ["python", "ProtestCrawler.py"]
