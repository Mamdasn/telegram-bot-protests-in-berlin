# syntax=docker/dockerfile:1

FROM python:3.11-alpine

WORKDIR /app

#RUN python3 -m pip install --upgrade pip
COPY . .

RUN pip3 install -r requirements.txt

# Create a directory in the container to log the output of the code
RUN mkdir -p /app/output

CMD ["sh", "-c", "python protestcrawler.py >> /app/output/protestcrawler.logs 2>&1"]
