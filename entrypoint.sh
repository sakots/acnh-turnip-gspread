#!/bin/sh
set -eux

. ./secret.env
python3 main.py --config config.yml
