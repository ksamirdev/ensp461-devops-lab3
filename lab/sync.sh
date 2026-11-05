#!/bin/bash
# Copies between this repo on the Mac and the lab machine (macOS keeps Desktop private from OrbStack).
# usage: lab/sync.sh to | back
M=ensp461-lab3; DIR='~/ensp461-lab3'
cd "$(dirname "$0")/.."
case "$1" in
  to)   COPYFILE_DISABLE=1 tar c --exclude .venv --exclude .git --exclude reports --exclude evidence . | orb -m $M bash -c "mkdir -p $DIR && tar xf - -C $DIR --warning=no-unknown-keyword" ;;
  back) orb -m $M bash -c "cd $DIR && tar c evidence \$(ls infra/.terraform.lock.hcl 2>/dev/null)" | tar xf - ;;
esac
