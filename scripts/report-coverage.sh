#!/usr/bin/env bash

set -e
set -x

if [ -n "$ENV" ]; then
  case "$ENV" in
  nocoverage) exit;;
  esac
fi

coverage report -m
coverage xml

curl -S -L --connect-timeout 5 --retry 6 -s https://codecov.io/bash -o codecov.sh
bash codecov.sh -Z -f coverage.xml
