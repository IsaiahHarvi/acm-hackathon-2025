#!/usr/bin/env python3

docker kill postgres
docker container rm postgres
docker image rm postgres
docker volume rm pgdata
