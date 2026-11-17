#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4", "requests"]
# ///
"""One-off: set "Link to > Enlarge on click" (lightbox) on every gallery and image block via REST.

Does what the block editor does (WP 7.1): a gallery gets linkTo=lightbox (block-library
getHrefAndDestination); every image block, inside a gallery or not, gets linkDestination=none,
lightbox.enabled=true and no <a> around the <img> (block-editor "Enlarge on click" menu item).
Single images linking to a custom URL keep their link. Classic [gallery] shortcodes and <img>
outside image blocks have no such setting; both are only reported.

Only posts that need the change are written. Re-serializing changes their markup in ways that
are equivalent for browsers and WP's block validation (blank lines between blocks, entities
written as characters, "/>" on void tags).

Dry run by default, --apply writes. WP keeps a revision of the new content only, so posts that
never had a revision cannot be rolled back: have a DB backup first.
Env: WP_URL, WP_USER, WP_APP_PASSWORD (as for wp2hugo.py).
"""

import json
import os
import sys
from argparse import ArgumentParser

import requests
from bs4 import BeautifulSoup, Comment, Tag
from bs4.dammit import EntitySubstitution
from bs4.formatter import HTMLFormatter


class KeepOrder(HTMLFormatter):
    """bs4's default formatter sorts attributes; keep them as written."""

    def attributes(self, tag):
        return tag.attrs.items()


FORMATTER = KeepOrder(entity_substitution=EntitySubstitution.substitute_xml, void_element_close_prefix="/")


def ser(attrs):
    """Block attribute JSON exactly like @wordpress/blocks serializeAttributes."""
    s = json.dumps(attrs, separators=(",", ":"), ensure_ascii=False)
    for a, b in (
        ("\\\\", "\\u005c"),
        ("--", "\\u002d\\u002d"),
        ("<", "\\u003c"),
        (">", "\\u003e"),
        ("&", "\\u0026"),
        ('\\"', "\\u0022"),
    ):
        s = s.replace(a, b)
    return s


def block(node):
    """(name, attrs) if node is an opening block comment like `wp:image {...}`, else None."""
    if not isinstance(node, Comment):
        return None
    name, _, js = node.strip().partition(" ")
    if not name.startswith("wp:") or js.endswith("/"):
        return None
    return name[3:], json.loads(js) if js else {}


def next_tag(node):
    for sib in node.next_siblings:
        if isinstance(sib, Tag):
            return sib
        if sib.strip():
            return None
    return None


def set_block(node, name, attrs):
    node.replace_with(Comment(f" wp:{name} {ser(attrs)} " if attrs else f" wp:{name} "))


def in_gallery(node):
    return node.parent.name == "figure" and "wp-block-gallery" in node.parent.get("class", [])


def lightbox(raw):
    """Content with lightbox on all galleries and image blocks; raw itself if nothing changes."""
    soup = BeautifulSoup(raw, "html.parser")
    changed = False
    for node in list(soup.find_all(string=lambda s: isinstance(s, Comment))):
        parsed = block(node)
        if not parsed:
            continue
        name, attrs = parsed
        if name == "gallery":
            new = {**attrs, "linkTo": "lightbox"}
        elif name == "image" and (in_gallery(node) or attrs.get("linkDestination") != "custom"):
            new = {k: v for k, v in attrs.items() if k != "href"}
            new.update(linkDestination="none", lightbox={**attrs.get("lightbox", {}), "enabled": True})
            figure = next_tag(node)
            link = figure.find("a") if figure else None
            if link and link.find("img"):
                link.unwrap()
                changed = True
        else:
            continue
        if new != attrs:
            set_block(node, name, new)
            changed = True
    return soup.decode(formatter=FORMATTER) if changed else raw


def stray_images(raw):
    """<img> not inside an image block's figure: no lightbox setting for those."""
    soup = BeautifulSoup(raw, "html.parser")
    count = 0
    for img in soup.find_all("img"):
        fig = img.find_parent("figure")
        prev = next((s for s in fig.previous_siblings if isinstance(s, Tag) or s.strip()), None) if fig else None
        if not (prev is not None and (block(prev) or ("",))[0] == "image"):
            count += 1
    return count


def items(s, api):
    page = 1
    while True:
        params = {"per_page": 100, "page": page, "status": "any", "context": "edit"}
        r = s.get(api, params=params, timeout=120)
        if not r.ok:
            sys.exit(f"GET {api}: {r.status_code} {r.text[:300]}")
        yield from r.json()
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            return
        page += 1


def main():
    p = ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("--url", default=os.environ.get("WP_URL"), help="WordPress base URL (default: $WP_URL)")
    p.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = p.parse_args()
    if not args.url:
        p.error("--url or WP_URL is required")
    user, password = os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD")
    if not (user and password):
        p.error("WP_USER and WP_APP_PASSWORD are required")
    s = requests.Session()
    s.auth = (user, password)
    for kind in ("posts", "pages"):
        api = args.url.rstrip("/") + f"/wp-json/wp/v2/{kind}"
        for item in items(s, api):
            raw, where = item["content"]["raw"], f"{item['id']} {item['link']}"
            if "[gallery" in raw:
                print(f"SKIP classic [gallery]: {where}", file=sys.stderr)
            if n := stray_images(raw):
                print(f"SKIP {n} <img> outside image blocks: {where}", file=sys.stderr)
            new = lightbox(raw)
            if new == raw:
                continue
            print(f"{'UPDATE' if args.apply else 'would update'}: {where}")
            if args.apply:
                r = s.post(f"{api}/{item['id']}", json={"content": new}, timeout=120)
                if not r.ok:
                    sys.exit(f"POST {item['id']}: {r.status_code} {r.text[:300]}")


if __name__ == "__main__":
    main()
