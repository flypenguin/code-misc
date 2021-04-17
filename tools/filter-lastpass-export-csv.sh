#!/usr/bin/env bash

# this file removes a line from a lastpass export CSV and saves it into
# an export file.
# why would we want that? because bitwarden has a maximum field size
# which is smaller than lastpass' one, so we need to filter out
# all the "too big entries" from the export csv in order to import
# them into bitwarden.
#
# PREREQUISITES: burntsushi / xsv

if [ -z "$2" ] ; then
  echo "USAGE:   $(basename $0) <csv-file> <filter-string>"
  echo "EXAMPLE: $(basename $0) lastpass-2021-01-01.csv \"my long login\""
  exit -1
fi

CSVFILE="$1"
FILTERSTR="$2"
FILEPART=$(echo $FILTERSTR | tr "[:upper:]" "[:lower:]" | sed -E 's/[^a-z0-9.-]+/-/g')
REMOVED_FILE="removed-$FILEPART.csv"
REM0="$(dirname "$0")/_$REMOVED_FILE"
REM1="$(dirname "$0")/$REMOVED_FILE"

if [ -f "$(dirname "$0")/$REMOVED_FILE" ] ; then
  echo "$REMOVED_FILE exists. aborting."
  exit -2
fi

xsv search -s name "$FILTERSTR" "$CSVFILE" > "$REM0"
LINES=$(xsv count "$REM0")
if (( $LINES != 1 )) ; then
  echo "ERROR: filtered records must be 1 (is: $LINES)"
  echo "Aborting."
  exit -3
fi
mv "$REM0" "$REM1"

TMPFILE=$(mktemp -p "$(dirname "$0")")
xsv search -vs name "$2" "$1" > "$TMPFILE"
mv -f "$TMPFILE" "$CSVFILE"

