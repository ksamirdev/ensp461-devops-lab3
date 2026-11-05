# usage: source lab/rec.sh <logfile>; rec <command...> - echoes and runs a command, appending real output to the log
LOG="$1"; mkdir -p "$(dirname "$LOG")"
rec() { echo "\$ $*" | tee -a "$LOG"; bash -c "$*" 2>&1 | tee -a "$LOG"; local rc=${PIPESTATUS[0]}; echo | tee -a "$LOG"; return $rc; }
