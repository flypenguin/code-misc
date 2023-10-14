#!/usr/bin/env bash

# prerequisites:
#   - ghostscript (from brew)

if [ -z "$1" ] ; then
    echo "USAGE: $(basename $0) FILE[, FILE...]"
    exit 255
fi

for file in "$@" ; do
    echo -n "Unprotecting $file ... "
    mv "$file" "$file.orig"
    \gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile="$file" -f "$file.orig"
    echo "done."
done
