#!/usr/bin/env bash

SLEEP=${1:-2}

# $1 - filename
do_ps() {
  ps -ao pid,command | grep -v "ps " > $1
}

do_ps pid0.txt
while true ; do
  sleep $SLEEP
  do_ps pid1.txt
  clear
  TS="# diff @ $(date)"
  DIFF=$(diff pid*.txt)
  echo -e "${TS}\n${DIFF}"
  [ -n "$DIFF" ] && echo -e "#\n${TS}\n#\n${DIFF}" > diff_$(date +%Y%m%d_%H%M%S).txt
  mv -f pid1.txt pid0.txt
done
