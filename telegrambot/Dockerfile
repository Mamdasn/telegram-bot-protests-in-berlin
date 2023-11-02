# syntax=docker/dockerfile:1

FROM python:3.11-alpine

# Install nginx
RUN apk --no-cache add nginx curl openssl

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 5000 5000

CMD ["python", "telegram-bot-run.py"]
