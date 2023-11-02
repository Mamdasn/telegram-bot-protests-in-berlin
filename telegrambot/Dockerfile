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

# Copy the content of the local src directory to the working directory
COPY . .

# Copy the Nginx configuration file
COPY portforwarding.conf /etc/nginx/nginx.conf

EXPOSE 443

# Create a directory in the container to log the output of the code
RUN mkdir -p /app/output

CMD ["python", "telegram-bot-run.py"]
