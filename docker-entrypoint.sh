#! /bin/bash

set -e

case "$1" in
  cat|sh|bash|python|ptipython) exec "$@" ;;
  *) exec python -m charybdisfs "$@" ;;
esac
