# syntax=docker/dockerfile:1

FROM python:3.11-alpine

# Install nginx
RUN apk --no-cache add nginx curl openssl

# Install necessary packages for building python packages
RUN apk --no-cache add gcc musl-dev libffi-dev libpq-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

EXPOSE 443

# Create a directory in the container to log the output of the code
RUN mkdir -p /app/output

# Make the nginx configuration script and telegram webhook script executable
RUN chmod +x initial-setup-files/nginx-setup.sh
RUN chmod +x initial-setup-files/webhook-setup.sh

# Specify the command to run on container start
CMD ["sh", "-c", "/app/initial-setup-files/webhook-setup.sh && /app/initial-setup-files/nginx-setup.sh && nginx && gunicorn -w 2 --bind 0.0.0.0:5000 wsgi:app >> /app/output/telegram.logs 2>&1"]
