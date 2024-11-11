# From ubuntu lts
FROM ubuntu:20.04

# Update and install required packages
RUN apt-get update && apt-get install -y \
python3 \
python3-pip \
vim

# Install Required Python Packages
RUN pip3 install paramiko

# Clean up to reduce image size
RUN apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Update and Upgrade Installed Packages to Latest Versions (if any)
RUN apt-get update && apt-get upgrade -y

# Copy app directory and files to /app in container
COPY app /app

#Make /data directory
RUN mkdir /data

# Set the working directory
WORKDIR /app

# Run mesh-monitor.py on startup
CMD ["python3", "backup-saves.py"]