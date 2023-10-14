# shell: /bin/bash
# params: as stdin
# prerequisites:
#   - parrallel (from brew)
# description:
#   mark any number of images in finder, and convert them into (see below)
#   web and jpg, with differing qualities, AND into different sizes.
# example:
#   image img1.jpg will be converted to:
#     - img1.1280px.q50.webp
#     - img1.1280px.q80.webp
#     - img1.1280px.q50.jpg
#     - img1.1280px.q80.jpg
#   it is only one size given, otherwise it'd be 8 images - 2 sizes for each
#   combination listed above, instead of one (assuming two sizes in total)
# IMPORTANT:
#   yes, the "cat > tmp" is weird, BUT IT DID NOT WORK OTHERWISE.


export PATH=$PATH:/usr/local/bin
export sizes="1280"
export qualities="50 80"
export formats="webp jpg"

TMP=$(mktemp)
cat > "$TMP"

parallel -r convert {1} -geometry "{4}x{4}\>" -quality {2} {1.}.{4}px.q{2}.{3} :::: "$TMP" ::: $qualities ::: $formats ::: $sizes

rm "$TMP"
