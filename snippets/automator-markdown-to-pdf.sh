# shell: /bin/bash
# params: stdin
# prerequisites:
#   - latex / mactex (from brew)
#   - pandoc (from brew)

export PATH="/Library/TeX/texbin:/usr/local/bin:/opt/homebrew/bin:$PATH"
while read infile ; do
    pandoc -f markdown -t pdf -o "${infile%.*}.pdf" "$infile"
done
