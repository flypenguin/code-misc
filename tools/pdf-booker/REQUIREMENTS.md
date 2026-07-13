# pdf-booker — Requirements

## Overview

CLI tool that binds pre-existing single-piece sheet-music PDFs into one printable
"book" PDF, with a table of contents, page numbers, and print-friendly layout.

- Language: Python
- Type: single-file script, `uv` shebang (`#!/usr/bin/env -S uv run`), inline
  script dependencies (PEP 723)

## Input

- Positional CLI arguments: any mix of PDF files and directories.
- Order matters: arguments are processed in the given order; a directory is
  expanded in place to its `*.pdf` files sorted alphabetically.
  - Example: `pdf-booker intro.pdf songs/ outro.pdf` → `intro.pdf`, then all
    PDFs in `songs/` alphabetically, then `outro.pdf`.
- Each input PDF is one "piece" (sheet note), 1..n pages.

## Output

- One merged PDF (default name: TBD, suggest `book.pdf`; overridable via `-o`).
- Structure: table of contents first, then the pieces.

## Table of contents

- Generated automatically, placed at the front of the book.
- Entry title: derived from the filename — extension stripped, leading numeric
  ordering prefix stripped (e.g. `03_Autumn Leaves.pdf` → "Autumn Leaves").
- Entry page number: the printed book page number where the piece starts.
- The TOC lists only the pieces (it does not list itself).

## Page numbering

- Every page is numbered by its position. The TOC is page 1 (the first
  right-hand page) and carries a printed number; the first sheet is page 2.
- Blank filler pages carry their page number too.
- Position: bottom outer corner (right edge on right/recto pages, left edge on
  left/verso pages).
- The number is printed on an opaque background (small filled box with padding),
  so it remains readable even if the original PDF has its own page number in
  the same spot.

## Layout (double-page / spread rules)

Standard bound-book model: odd physical pages are on the RIGHT (recto), even on
the LEFT (verso); open spreads are (2,3), (4,5), (6,7), … So a two-page piece is
fully visible on one open spread only if it starts on a LEFT (even) page.

- The TOC occupies physical page 1 (a right-hand page).
- The first sheet starts on the next LEFT page, directly facing the TOC — no
  wasted blank for a single-page TOC.
- Every multi-page piece starts on a LEFT page, so its first two pages share one
  spread. A blank page is inserted before it when needed to achieve this.
- Single-page pieces have no double-page requirement and simply fill the next
  available page, so two consecutive single-pagers naturally share a spread.

## Page resizing

- Every page is resized to a target paper format, default A4 (portrait).
- Format selectable via CLI flag (at minimum: A4, Letter).
- Content is scaled to fit, aspect ratio preserved, centered.

## Suggested additional features (not confirmed)

- **PDF outline/bookmarks** mirroring the TOC — cheap to add, helps on-screen use.
- **PDF metadata**: set document title (e.g. from `--title` flag).
- **`--dry-run`**: print resulting piece order, page counts, and inserted
  blanks without writing the output.
- **Overwrite protection**: refuse to overwrite existing output unless `--force`.
- **Optional cover/title page** via `--title`.

## Open questions & preliminary answers

- Default output filename?
  - defined by "-o/--out" parameter
- Cover page wanted at all?
  - use TOC for now
- Landscape source pages: rotate to portrait, or scale-to-fit as-is?
  - stop processing, no landscape
- Should blank filler pages be truly blank, or carry the page number?
  - carry page number
