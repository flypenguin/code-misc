# shell: /bin/bash
# params: as stdin
# prerequisites:
#   - parrallel (from brew)
# description:
#   mark any number of images in finder, and convert them into (see below)
#   web and jpg, with differing qualities.
# example:
#   - image img1.jpg will be converted to:
#     - img1.q50.webp
#     - img1.q80.webp
#     - img1.q50.jpg
#     - img1.q80.jpg
# IMPORTANT:
#   yes, the "cat > tmp" is weird, BUT IT DID NOT WORK OTHERWISE.

export PATH=$PATH:/usr/local/bin

TMP=$(mktemp)
cat > "$TMP"
parallel -r convert {1} -quality {2} {1.}.q{2}.{3} :::: "$TMP" ::: 50 80 ::: webp jpg
rm "$TMP"
