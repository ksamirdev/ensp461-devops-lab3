#!/bin/bash
# macOS blocks OrbStack from reading ~/Desktop, so Docker runs from a copy in ~/lab3-run.
# usage: lab/sync.sh to   - copy project to run dir
#        lab/sync.sh back - copy evidence and lock file back to the repo
REPO="$(cd "$(dirname "$0")/.." && pwd)"; RUN="$HOME/lab3-run"
case "$1" in
  to)   rsync -a --exclude .venv --exclude .git --exclude evidence --exclude reports "$REPO/" "$RUN/"; mkdir -p "$RUN/evidence" ;;
  back) rsync -a "$RUN/evidence/" "$REPO/evidence/"; [ -f "$RUN/infra/.terraform.lock.hcl" ] && cp "$RUN/infra/.terraform.lock.hcl" "$REPO/infra/" ;;
esac
