# Implementation decisions — first working version

Notes on choices made while implementing `pdf-booker.py`, for later review.
Each has a **why** and, where relevant, a flag if it contradicts or extends the
spec so it can be confirmed.

## Libraries

- **pypdf** (read/merge/transform pages) + **reportlab** (generate TOC pages and
  the page-number overlays). Both pinned loosely in the PEP 723 header
  (`pypdf>=5`, `reportlab>=4`). Dev used a local `.venv` (uv); nothing installed
  globally. The shebang `#!/usr/bin/env -S uv run --script` + inline deps make it
  runnable standalone.

## Left/right convention — standard bound book

- Odd physical index = RIGHT (recto), even physical index = LEFT (verso). Open
  spreads are `(2,3), (4,5), (6,7)…`, so a two-page piece is fully visible on one
  spread only if it starts on a **LEFT (even)** page.
- **The TOC is physical page 1 — a right-hand page.** The first sheet then
  starts on the facing **LEFT** page (physical 2 for a single-page TOC), so it is
  spread-aligned from its first page and no blank is wasted between TOC and
  content.
- Page number outer corner follows from this: RIGHT/recto pages get the number
  bottom-right, LEFT/verso pages bottom-left. So printed page 1 (first sheet, a
  verso) carries its number bottom-left.

## Layout / packing

- After the TOC, a `front_blank` (unnumbered) is inserted **only if** the TOC has
  an even page count (so content still lands on a LEFT verso). For the usual
  single-page TOC there is no blank at all.
- **Multi-page pieces start on a LEFT (verso/even) page** so their first two
  pages share one open spread; a `fill_blank` (numbered) is inserted before them
  when the next slot is a right page. This applies uniformly to every piece
  including the first — no special case.
- **Single-page pieces** have no double-page need, so they simply fill the next
  slot. Two consecutive single-pagers therefore share a spread automatically, and
  a single after a multi-page piece fills the free right page with no wasted
  blank.

## Accented filenames (Queensrÿche)

- macOS returns filenames in Unicode **NFD** (decomposed): `ÿ` arrives as `y` +
  U+0308 combining diaeresis, which has no standalone glyph → rendered as a black
  box. Fix: `unicodedata.normalize("NFC", stem)` composes it back to `ÿ`
  (U+00FF), which the base Helvetica font renders correctly *with* the diaeresis
  (verified). No custom font needed. If a title ever contains a character outside
  Helvetica's WinAnsi/Latin-1 range, that would need an embedded font (e.g. a
  bundled Noto/serif) — not required for the current material.

## Page numbering

- **Every page is numbered by its physical position.** The TOC is page 1 (the
  first right-hand page) and carries a printed "1"; the first sheet is page 2.
  Blank pages (front/fill) carry their number too.
- The TOC entry numbers therefore point at each piece's physical page (first
  sheet = 2, etc.).
- Position: bottom **outer** corner (right edge on recto/right pages, left edge
  on verso/left pages), `18pt` from the edges. Page 1 (TOC, recto) prints its
  number bottom-right; page 2 (first sheet, verso) bottom-left.
- Drawn on an **opaque white box** (`3pt` padding) so it survives on top of any
  page number already present in the source.

## Titles

- From filename: extension stripped, then a leading numeric prefix removed via
  `^\s*\d+\s*[._\-–—)\]]*\s*` (handles `03_`, `12 - `, `4.`, `5)`…). Falls back to
  the raw stem if stripping would empty it.

## Resizing

- Every page scaled to the target format (A4 default, Letter available),
  **aspect ratio preserved, centered**. Source `/Rotate` is normalised into the
  content first (`transfer_rotation_to_content`); mediabox offset handled so
  pages whose origin isn't (0,0) still center correctly.
- **Landscape pages abort** the run with an error (per your answer), detected on
  the effective (rotation-aware) size.

## TOC

- Auto-generated, placed first. Rows-per-page computed from page height; entry
  count → TOC page count is computed up front (independent of content numbers),
  so no circular dependency. Dotted leader between title and page number; long
  titles are truncated to fit.
- TOC page count is treated as authoritative: if reportlab renders fewer/more
  pages than reserved, output is padded/truncated so physical indices stay valid.
  (Not expected to trigger with the current row math; a safety net.)

## Extras implemented (were "suggested, unconfirmed")

- **PDF outline/bookmarks** mirroring the TOC (one entry per piece → its first
  page).
- **`--title`** sets PDF metadata `/Title`.
- **`--dry-run`** prints the planned layout (physical page, L/R, number, piece).
- **`--force`** required to overwrite an existing output; otherwise it errors.
- No cover page (you said "use TOC for now").

## CLI summary

```
pdf-booker.py [inputs…] -o OUT [-f A4|LETTER] [-t TITLE] [--dry-run] [--force]
```

`inputs` are files and/or directories in order; directories expand in place to
their `*.pdf` sorted case-insensitively.

## Known limitations / open for review

- Page 1 is the **TOC** (right-hand); the first sheet is page 2 on the facing
  left-hand page. This keeps multi-page pieces spread-aligned with no wasted
  blank.
- Encrypted/password PDFs not handled (would raise from pypdf).
- Some source PDFs emit `Ignoring wrong pointing object …` warnings from pypdf on
  stderr; they are harmless (pypdf recovers) and do not affect the output.
- Very long piece titles are truncated in the TOC rather than wrapped.
- Source pages already smaller/larger than target are scaled to fit; no option
  yet to leave small pages un-upscaled.
- Case-insensitive alphabetical sort for directory expansion (e.g. so `a.pdf`
  and `B.pdf` order naturally); confirm if you want strict byte ordering.
