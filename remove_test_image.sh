#!/bin/bash

# Remove existing Retropie Backup Docker containers and images launched in separate docker compose files
printf "\n\n\n***************************************************\n"
printf "Removing existing Retropie Backup Docker containers and images...\n"
printf "***************************************************\n\n\n"
docker stop $(docker ps -a | grep retropie_backup | awk '{print $1}')
docker rm $(docker ps -a | grep retropie_backup | awk '{print $1}')
docker rmi $(docker images | grep retropie_backup | awk '{print $3}')

docker image ls | grep retropie
docker ps -a | grep retropie