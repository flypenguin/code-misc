# pdf-booker

Bind a set of single-piece sheet-music PDFs into one printable "book": a table
of contents, page numbers, and a print-friendly double-page layout.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — that's it. The script declares its own
  dependencies (`pypdf`, `reportlab`) inline (PEP 723) and `uv` installs them in
  an isolated, cached environment on first run. Nothing is installed globally.

## Usage

```sh
./pdf-booker.py INPUT [INPUT ...] -o BOOK.pdf
```

`INPUT` may be a PDF file or a directory. Arguments are processed **in order**;
a directory is expanded in place to its `*.pdf` files sorted alphabetically.

```sh
# One directory of pieces
./pdf-booker.py Bind/ -o book.pdf

# Explicit order: a file, then a folder, then another file
./pdf-booker.py intro.pdf songs/ outro.pdf -o book.pdf

# Preview the layout without writing anything
./pdf-booker.py Bind/ --dry-run
```

If the shebang isn't executable on your system, run it via `uv` directly:

```sh
uv run --script pdf-booker.py Bind/ -o book.pdf
```

## Options

| Option               | Description                                            |
| -------------------- | ------------------------------------------------------ |
| `-o`, `--out PATH`   | Output PDF path (required unless `--dry-run`).         |
| `-f`, `--format FMT` | Paper size: `A4` (default) or `LETTER`.                |
| `-t`, `--title TEXT` | Document title stored in the PDF metadata.             |
| `--dry-run`          | Print the planned page layout and exit; write nothing. |
| `--force`            | Overwrite the output file if it already exists.        |

## What it produces

- **Table of contents** on page 1 (the first right-hand page), with one entry
  per piece and its page number. Titles come from the filenames, with any
  leading numeric ordering prefix stripped (`03_Autumn Leaves.pdf` → "Autumn
  Leaves").
- **Page numbers** on every page, in the bottom outer corner, on an opaque
  background so they stay readable over any numbering already in the source.
- **Double-page layout**: every multi-page piece starts on a left-hand page so
  it is fully visible across one open spread; single-page pieces pack two to a
  spread. Blank pages are inserted only where needed.
- **PDF bookmarks** mirroring the table of contents.
- Every page is **resized** to the target format, aspect ratio preserved and
  centered.

## Notes & limits

- Landscape source pages are **not** supported; the run stops with an error.
- Encrypted / password-protected PDFs are not handled.
- Some source PDFs print harmless `Ignoring wrong pointing object …` warnings
  from the PDF library; they do not affect the output.

See `REQUIREMENTS.md` for the full specification and `DECISIONS.md` for the
rationale behind the layout and numbering choices.
