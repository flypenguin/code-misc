# shell: /bin/bash
# params: as params
# description:
#   opens an app (here: vscodium) in a given path
#   (not as useful as you might think, cause if you click on an empty
#   space in finder, you will _not_ get the "quick actions" ...)

PATH=/usr/local/bin:/opt/homebrew/bin:$PATH
# easier to switch to/from VSCode etc.
APP=codium

for f in "$@"
do
    "$APP" "$f"
done
