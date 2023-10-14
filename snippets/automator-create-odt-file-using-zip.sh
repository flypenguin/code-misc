# shell: /bin/bash
# params: as stdin
# notes:
#   - you must not include any extra files.
#     - really, don't.
#     - .DS_Store is deadly.
#     - if the file is "corrupt", i'd start there.

SAVE_DIR="$PWD"

while read input_dir ; do
	[[ -d "$input_dir" ]] || continue

	cd "$input_dir"

	# https://stackoverflow.com/a/315113
	touch _odt_create_log.txt
	exec > _odt_create_log.txt
	exec 2>&1

	set -x
	ODT_FILE="../$(basename "$input_dir").odt"
	rm -f "$ODT_FILE"

	# create ODT documents with ZIP: https://is.gd/TZmNOQ
	# SOME NOTES:
	#    - YES, the parameter order in 2nd command MATTERS!!
	#    - NO EXTRA FILES (e.g. the log file) in the .odt document
	zip      "$ODT_FILE" -0 mimetype
	zip -ruo "$ODT_FILE"    .         -x mimetype _odt_create_log.txt \*.DS_Store

	cd "$SAVE_DIR"
	set +x
done
