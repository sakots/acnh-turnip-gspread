#!/usr/bin/env bash

set -e

echo "Creating mongo users..."
mongo admin --host localhost \
  -u "$MONGO_INITDB_ROOT_USERNAME" \
  -p "$MONGO_INITDB_ROOT_PASSWORD" \
  --eval "db.createUser({user: '$MONGO_APP_USERNAME', pwd: '$MONGO_APP_PASSWORD', roles: [{role: 'readWrite', db: 'turnip_bot'}]});"
echo "Mongo users created."
