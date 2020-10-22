#! /bin/bash

set -e

export PYTHONPATH=/src

case "$1" in
  cat|sh|bash|python) exec "$@" ;;
  *) exec python -m charybdisfs "$@" ;;
esac
