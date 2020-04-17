#!/bin/sh
set -eux

. ./secret.sh
python3 main.py --config config.yml
