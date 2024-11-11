#!/bin/bash

# git pull
printf "\n\n\n***************************************************\n"
printf "Pulling the latest changes from the repository...\n"
printf "***************************************************\n\n\n"
git pull

# Remove existing Retropie Backup Docker containers and images launched in separate docker compose files
printf "\n\n\n***************************************************\n"
printf "Removing existing Retropie Backup Docker containers and images...\n"
printf "***************************************************\n\n\n"
docker stop $(docker ps -a | grep retropie_backup | awk '{print $1}')
docker rm $(docker ps -a | grep retropie_backup | awk '{print $1}')
docker rmi $(docker images | grep retropie_backup | awk '{print $3}')

# Build the Docker image
printf "\n\n\n***************************************************\n"
printf "Building the Docker image...\n"
printf "***************************************************\n\n\n"
docker build -t retropie_backup .

docker image ls | grep retropie
ls -la

# Run Docker Compose in detached mode
printf "\n\n\n***************************************************\n"
printf "Running Docker Compose in detached mode...\n"
printf "***************************************************\n\n\n"
docker compose up -d

# run docker logs -f
printf "\n\n\n***************************************************\n"
printf "Running docker logs -f...\n"
printf "***************************************************\n\n\n"
tail -f -n 40 /docker/retropie_backup/data/retropie_backup.log