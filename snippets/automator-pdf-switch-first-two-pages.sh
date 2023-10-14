# shell: /bin/bash
# params: as params
# prerequisites:
#   - pdftk (from brew, probably)
# description:
#   this script ...
#     - extracts page 1 and 2 from a pdf document
#     - then switches their order
#   example:
#     - a pdf document with pages p1 p2 p3 p4 p5 ...
#     - ... will become: p2 p1 (end)

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
	pdftk A="$ORIG_FILE" cat A2 A1 output "$f"
done
