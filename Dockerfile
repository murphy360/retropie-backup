# From ubuntu lts
FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
python3 \
python3-pip \
vim

# Install Required Python Packages
RUN pip3 install paramiko \
logging \
datetime

# Copy app directory and files to /app in container
COPY app /app

# Copy data directory to /data
COPY data /data

# Set the working directory
WORKDIR /app

# Run mesh-monitor.py on startup
CMD ["python3", "backup-saves.py"]