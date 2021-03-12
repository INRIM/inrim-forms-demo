#!/bin/bash
if [ -d "$PWD/app/themes" ]; then
      git -C "$PWD/app/themes" pull
  else
      git -C "$PWD/app" clone https://github.com/INRIM/forms-theme-italia.git themes

fi
if [ ! -f ".env-test" ]; then
    echo ".env-test File not found!"
    exit 0
fi
docker-compose -f docker-compose-dev.yml stop
docker-compose -f docker-compose-dev.yml -p forms-inrim up --force-recreate --detach --remove-orphans