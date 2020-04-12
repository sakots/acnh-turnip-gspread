#!/bin/sh
set -eux
. ./secret.env
docker-compose build
docker-compose up -d
