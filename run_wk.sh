#!/bin/bash
# Rebuild and restart the worker

docker-compose build worker
docker-compose up -d --no-deps worker
