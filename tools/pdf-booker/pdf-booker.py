#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pypdf>=5",
#     "reportlab>=4",
# ]
# ///
"""pdf-booker — bind single-piece sheet-music PDFs into one printable book.

See REQUIREMENTS.md for the full specification.

Layout model (standard bound book; see DECISIONS in the repo notes):
  Odd physical index = RIGHT (recto), even physical index = LEFT (verso).
  Open spreads are (2,3), (4,5), (6,7), ... so a two-page piece is fully
  visible on one spread only if it starts on a LEFT (even) page.

  - The TOC is physical page 1 (a right-hand page) and is itself numbered;
    the first sheet is page 2. Every page is numbered by its position.
  - The first sheet starts on the LEFT page facing the TOC (no wasted blank
    for a single-page TOC).
  - Every multi-page piece starts on a LEFT page; a blank is inserted before
    it when needed.
  - Single-page pieces fill the next slot, so two of them share a spread.
  - Outer corner for the page number: RIGHT pages bottom-right, LEFT pages
    bottom-left.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import unicodedata
from io import BytesIO
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas

PAGE_SIZES = {"A4": A4, "LETTER": LETTER}

# --- geometry (points; 1pt = 1/72 inch) -------------------------------------
EDGE_MARGIN = 18.0  # distance of the page-number box from the page edges
BOX_PAD = 3.0  # padding inside the opaque number box
NUM_FONT = "Helvetica"
NUM_SIZE = 10.0

TOC_TITLE_FONT = "Helvetica-Bold"
TOC_TITLE_SIZE = 20.0
TOC_ENTRY_FONT = "Helvetica"
TOC_ENTRY_SIZE = 12.0
TOC_LEADING = 22.0
TOC_TOP_MARGIN = 60.0  # space reserved for the "Contents" heading
TOC_BOTTOM_MARGIN = 50.0
TOC_SIDE_MARGIN = 50.0


# --- input expansion --------------------------------------------------------
def expand_inputs(args: list[str]) -> list[Path]:
    """Turn positional args (files and/or dirs) into an ordered list of PDFs.

    Files are taken as-is; directories are expanded in place to their *.pdf
    files sorted case-insensitively by name.
    """
    pdfs: list[Path] = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            found = sorted(p.glob("*.pdf"), key=lambda x: x.name.lower())
            if not found:
                print(f"warning: no PDFs in directory {p}", file=sys.stderr)
            pdfs.extend(found)
        elif p.is_file():
            if p.suffix.lower() != ".pdf":
                sys.exit(f"error: not a PDF file: {p}")
            pdfs.append(p)
        else:
            sys.exit(f"error: no such file or directory: {p}")
    return pdfs


def title_from_filename(path: Path) -> str:
    """Strip extension and a leading numeric ordering prefix.

    '03_Autumn Leaves.pdf' -> 'Autumn Leaves'
    '12 - Yesterday.pdf'    -> 'Yesterday'

    The stem is normalised to NFC so accented letters that the filesystem
    stores decomposed (macOS: 'ÿ' as 'y' + combining diaeresis) compose into
    single glyphs the base font can render.
    """
    stem = unicodedata.normalize("NFC", path.stem)
    stem = re.sub(r"^\s*\d+\s*[._\-–—)\]]*\s*", "", stem)
    return stem.strip() or unicodedata.normalize("NFC", path.stem)


# --- piece / page model -----------------------------------------------------
class Piece:
    def __init__(self, path: Path):
        self.path = path
        self.title = title_from_filename(path)
        self.reader = PdfReader(str(path))
        self.pages = list(self.reader.pages)

    @property
    def n_pages(self) -> int:
        return len(self.pages)


def effective_size(page: PageObject) -> tuple[float, float]:
    """Width/height as visually seen, accounting for the /Rotate flag."""
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)
    rot = (page.get("/Rotate") or 0) % 360
    if rot in (90, 270):
        w, h = h, w
    return w, h


# --- layout planning --------------------------------------------------------
# Each slot describes one physical output page.
#   kind: 'toc' | 'front_blank' | 'content' | 'fill_blank'
#   piece/page_index set for 'content'
#   number: printed page number (= physical position; every page is numbered)
class Slot:
    def __init__(self, kind, piece=None, page_index=None):
        self.kind = kind
        self.piece = piece
        self.page_index = page_index
        self.number: int | None = None


def plan_layout(pieces: list[Piece], toc_pages: int) -> list[Slot]:
    """Build the ordered list of physical output slots.

    Even 1-based physical index == LEFT (verso); odd == RIGHT (recto). The TOC
    occupies the first physical page(s) (a right-hand page 1). Content then
    starts on a LEFT page so that multi-page pieces are visible on one spread.
    """
    slots: list[Slot] = [Slot("toc") for _ in range(toc_pages)]

    # Parity blank so the first sheet lands on a LEFT (verso, even) page,
    # directly facing the TOC with no wasted page. Only needed when the TOC
    # ends on a verso (even page count).
    if (len(slots) + 1) % 2 == 1:  # next index would be odd (right)
        slots.append(Slot("front_blank"))

    for piece in pieces:
        next_index = len(slots) + 1
        on_left = next_index % 2 == 0  # even physical index == LEFT (verso)

        # Multi-page pieces must start on a LEFT page so their first two pages
        # share one open spread; a blank is inserted if we are on a right page.
        # Single-page pieces have no such need and simply fill the next slot
        # (so two of them naturally share a spread).
        if piece.n_pages > 1 and not on_left:
            slots.append(Slot("fill_blank"))

        for i in range(piece.n_pages):
            slots.append(Slot("content", piece=piece, page_index=i))

    # Every physical page is numbered by its position: the TOC is page 1 (the
    # first right-hand page), the first sheet is page 2, and so on. Blanks carry
    # their number too.
    for i, s in enumerate(slots):
        s.number = i + 1
    return slots


def toc_rows_per_page(page_h: float) -> int:
    usable = page_h - TOC_TOP_MARGIN - TOC_BOTTOM_MARGIN
    return max(1, int(usable // TOC_LEADING))


# --- rendering --------------------------------------------------------------
def render_number_overlay(size, number: int, is_left: bool) -> PageObject:
    """A transparent page carrying just the page number in an opaque box."""
    w, h = size
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=size)
    c.setFont(NUM_FONT, NUM_SIZE)
    text = str(number)
    tw = c.stringWidth(text, NUM_FONT, NUM_SIZE)
    th = NUM_SIZE

    box_w = tw + 2 * BOX_PAD
    box_h = th + 2 * BOX_PAD
    if is_left:
        box_x = EDGE_MARGIN
    else:
        box_x = w - EDGE_MARGIN - box_w
    box_y = EDGE_MARGIN

    c.setFillColorRGB(1, 1, 1)
    c.rect(box_x, box_y, box_w, box_h, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(box_x + BOX_PAD, box_y + BOX_PAD, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def render_toc_pages(entries: list[tuple[str, int]], size) -> list[PageObject]:
    """entries: list of (title, printed_page_number)."""
    w, h = size
    rows = toc_rows_per_page(h)
    pages: list[PageObject] = []
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=size)

    idx = 0
    while idx < len(entries) or not pages and not entries:
        # heading
        c.setFont(TOC_TITLE_FONT, TOC_TITLE_SIZE)
        c.drawString(TOC_SIDE_MARGIN, h - TOC_TOP_MARGIN + 10, "Contents")
        y = h - TOC_TOP_MARGIN - TOC_LEADING
        for _ in range(rows):
            if idx >= len(entries):
                break
            title, pageno = entries[idx]
            c.setFont(TOC_ENTRY_FONT, TOC_ENTRY_SIZE)
            num = str(pageno)
            num_w = c.stringWidth(num, TOC_ENTRY_FONT, TOC_ENTRY_SIZE)
            # title (truncate if absurdly long)
            max_title_w = w - 2 * TOC_SIDE_MARGIN - num_w - 20
            title_draw = title
            while c.stringWidth(title_draw, TOC_ENTRY_FONT, TOC_ENTRY_SIZE) > max_title_w and len(title_draw) > 1:
                title_draw = title_draw[:-1]
            c.drawString(TOC_SIDE_MARGIN, y, title_draw)
            c.drawRightString(w - TOC_SIDE_MARGIN, y, num)
            # dotted leader
            lead_start = TOC_SIDE_MARGIN + c.stringWidth(title_draw, TOC_ENTRY_FONT, TOC_ENTRY_SIZE) + 5
            lead_end = w - TOC_SIDE_MARGIN - num_w - 5
            if lead_end > lead_start:
                c.setDash(1, 3)
                c.line(lead_start, y + 3, lead_end, y + 3)
                c.setDash()
            y -= TOC_LEADING
            idx += 1
        c.showPage()
        if not entries:
            break
    c.save()
    buf.seek(0)
    for pg in PdfReader(buf).pages:
        pages.append(pg)
    return pages


def compose_content_page(src: PageObject, size) -> PageObject:
    """Scale a source page to `size`, aspect-fit and centered."""
    tw, th = size
    src.transfer_rotation_to_content()
    sw = float(src.mediabox.width)
    sh = float(src.mediabox.height)
    ox = float(src.mediabox.left)
    oy = float(src.mediabox.bottom)

    scale = min(tw / sw, th / sh)
    dx = (tw - sw * scale) / 2
    dy = (th - sh * scale) / 2

    dest = PageObject.create_blank_page(width=tw, height=th)
    op = Transformation().translate(-ox, -oy).scale(scale).translate(dx, dy)
    dest.merge_transformed_page(src, op)
    return dest


def blank_page(size) -> PageObject:
    return PageObject.create_blank_page(width=size[0], height=size[1])


# --- orchestration ----------------------------------------------------------
def check_no_landscape(pieces: list[Piece]) -> None:
    for piece in pieces:
        for i, page in enumerate(piece.pages):
            w, h = effective_size(page)
            if w > h:
                sys.exit(f"error: landscape page not supported: {piece.path.name} page {i + 1} ({w:.0f}x{h:.0f})")


def print_dry_run(slots: list[Slot], pieces: list[Piece], toc_pages: int) -> None:
    print(f"pieces: {len(pieces)}   toc pages: {toc_pages}   physical pages: {len(slots)}")
    print("-" * 60)
    for i, s in enumerate(slots, start=1):
        side = "R" if i % 2 == 1 else "L"  # odd physical index == recto/right
        num = f"#{s.number}" if s.number else "  "
        if s.kind == "content":
            desc = f"{s.piece.title} (p{s.page_index + 1}/{s.piece.n_pages})"
        else:
            desc = f"[{s.kind}]"
        print(f"  phys {i:3d} {side} {num:>4}  {desc}")


def build(slots: list[Slot], pieces: list[Piece], size, out: Path, doc_title: str | None) -> None:
    writer = PdfWriter()

    # TOC entries: title -> first printed page number of each piece.
    entries: list[tuple[str, int]] = []
    first_slot_of_piece: dict[int, int] = {}
    for i, s in enumerate(slots):
        if s.kind == "content" and s.page_index == 0:
            entries.append((s.piece.title, s.number))
            first_slot_of_piece[id(s.piece)] = i

    toc_size = size
    # slot list already reserved the right number of TOC pages
    toc_pages = sum(1 for s in slots if s.kind == "toc")
    toc_rendered = render_toc_pages(entries, toc_size)
    # If rendering produced a different count than reserved, trust the reserved
    # count (padding/truncating) so physical indices stay valid.
    while len(toc_rendered) < toc_pages:
        toc_rendered.append(blank_page(size))
    toc_rendered = toc_rendered[:toc_pages]

    toc_iter = iter(toc_rendered)
    for s in slots:
        if s.kind == "toc":
            writer.add_page(next(toc_iter))
        elif s.kind in ("front_blank", "fill_blank"):
            writer.add_page(blank_page(size))
        else:  # content
            page = compose_content_page(s.piece.pages[s.page_index], size)
            writer.add_page(page)

    # Second pass: stamp page numbers (needs final physical index = position).
    for pos, s in enumerate(slots):
        if s.number is None:
            continue
        is_left = (pos + 1) % 2 == 0  # even physical index == LEFT (verso)
        overlay = render_number_overlay(size, s.number, is_left)
        writer.pages[pos].merge_page(overlay)

    # Outline / bookmarks mirroring the TOC.
    for i, s in enumerate(slots):
        if s.kind == "content" and s.page_index == 0:
            writer.add_outline_item(s.piece.title, i)

    if doc_title:
        writer.add_metadata({"/Title": doc_title})

    with open(out, "wb") as fh:
        writer.write(fh)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="pdf-booker",
        description="Bind single-piece PDFs into one printable book.",
    )
    ap.add_argument("inputs", nargs="+", help="PDF files and/or directories, in order")
    ap.add_argument("-o", "--out", help="output PDF path")
    ap.add_argument(
        "-f", "--format", default="A4", choices=list(PAGE_SIZES.keys()), help="target paper format (default: A4)"
    )
    ap.add_argument("-t", "--title", help="document title (PDF metadata)")
    ap.add_argument("--dry-run", action="store_true", help="print planned layout, write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite existing output file")
    args = ap.parse_args()

    size = PAGE_SIZES[args.format.upper()]

    pdf_paths = expand_inputs(args.inputs)
    if not pdf_paths:
        sys.exit("error: no input PDFs found")

    pieces = [Piece(p) for p in pdf_paths]
    check_no_landscape(pieces)

    # TOC page count depends only on the number of entries.
    rows = toc_rows_per_page(size[1])
    toc_pages = max(1, math.ceil(len(pieces) / rows))

    slots = plan_layout(pieces, toc_pages)

    if args.dry_run:
        print_dry_run(slots, pieces, toc_pages)
        return

    if not args.out:
        sys.exit("error: -o/--out is required (or use --dry-run)")
    out = Path(args.out)
    if out.exists() and not args.force:
        sys.exit(f"error: {out} exists (use --force to overwrite)")

    build(slots, pieces, size, out, args.title)
    print(f"wrote {out}  ({len(slots)} pages, {len(pieces)} pieces)")


if __name__ == "__main__":
    main()
