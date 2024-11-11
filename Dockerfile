# From ubuntu lts
FROM ubuntu:20.04

# Update and upgrade the system
RUN apt-get update && apt-get upgrade -y

# Install required packages
RUN apt-get install -y \
python3 \
python3-pip \
vim

# Install Required Python Packages
RUN pip3 install paramiko

# Clean up to reduce image size
RUN apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy app directory and files to /app in container
COPY app /app

#Make /data directory
RUN mkdir /data

# Set the working directory
WORKDIR /app

# Run mesh-monitor.py on startup
CMD ["python3", "backup-saves.py"]