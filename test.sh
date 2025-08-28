#!/usr/bin/env bash
set -eo pipefail

COLOR_GREEN=`tput setaf 2;`
COLOR_NC=`tput sgr0;` # No Color

echo "Starting black"
black .
echo "OK"

echo "Starting isort"
isort .
echo "OK"

echo "Starting mypy"
mypy .
echo "OK"
