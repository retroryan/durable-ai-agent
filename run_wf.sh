#!/bin/bash
# Rebuild and restart the API server

docker-compose build api
docker-compose up -d --no-deps api
