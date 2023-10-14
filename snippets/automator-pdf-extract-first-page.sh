# shell: /bin/bash
# params: as params
# prerequisites:
#   - ghostscript (from brew)
# description:
#   this script will ONLY KEEP the first page of a PDF document, or
#   put differently: it will delete all pages, starting with page 2.

export PATH=$PATH:/usr/local/bin
for f in "$@"
do
    BASE=${f%.*}
    EXT=${f##*.}
    ORIG_FILE="$BASE.orig.$EXT"
    COUNT=0
    while [ -f "$ORIG_FILE" ] ; do
        COUNT=$(($COUNT + 1))
        ORIG_FILE="$BASE.orig.$COUNT.$EXT"
    done
    mv "$f" "$ORIG_FILE"
	/usr/local/bin/gs -o "$f" -sDEVICE=pdfwrite -dFirstPage=2 "$ORIG_FILE"
done
