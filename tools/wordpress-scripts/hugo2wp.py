#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown", "pyyaml", "requests"]
# ///
"""Push Hugo page bundles (content/posts/**/index.md) into WordPress via REST API.

Auth: WordPress application password (Users > Profile > Application Passwords),
passed as WP_USER / WP_APP_PASSWORD env vars.

Re-runnable: a post whose slug already exists in WordPress is skipped.
Internal links ({{< relref >}}) point at the Hugo URL path, so set WP permalinks to
/%year%/%monthnum%/%day%/%postname%/ to keep them working.
"""

import html
import json
import mimetypes
import os
import re
import sys
from argparse import ArgumentParser
from datetime import timezone
from pathlib import Path

import markdown
import requests
import yaml

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
RE_REF = re.compile(r'\{\{<\s*(?:rel)?ref\s+"?([^"\s>]+)"?\s*>\}\}')
RE_FIGURE = re.compile(r"\{\{<\s*figure\s+(.*?)/?>\}\}")
RE_GALLERY = re.compile(r"\{\{<\s*lightgallery\b.*?>\}\}")
RE_YOUTUBE = re.compile(r'\{\{<\s*youtube\s+"?([\w-]+)"?\s*>\}\}')
RE_ATTR = re.compile(r'(\w+)="([^"]*)"')


def read_bundle(index_md):
    text = index_md.read_text()
    _, fm, body = text.split("---\n", 2)
    return yaml.safe_load(fm), body


def slug_of(bundle_dir, fm):
    if fm.get("url"):
        return fm["url"].strip("/").rsplit("/", 1)[-1]
    return DATE_PREFIX.sub("", bundle_dir.name)


def url_of(bundle_dir, fm):
    if fm.get("url"):
        return fm["url"]
    return f"/{fm['date']:%Y/%m/%d}/{slug_of(bundle_dir, fm)}/"


def convert(body, media, urls):
    """Hugo markdown -> WP HTML. media: bundle-relative path -> (id, url); urls: bundle name -> link."""

    def ref(m):
        name = m.group(1).rstrip("/").removesuffix("/index.md").removesuffix(".md").rsplit("/", 1)[-1]
        if name not in urls:
            print(f"  WARN: unresolved ref {m.group(1)}", file=sys.stderr)
        return urls.get(name, m.group(1))

    def figure(m):
        a = dict(RE_ATTR.findall(m.group(1)))
        src = media.get(a.get("src", ""), (None, a.get("src", "")))[1]
        width = f' style="width:{a["width"]}"' if "width" in a else ""
        cap = f"<figcaption>{a['caption']}</figcaption>" if "caption" in a else ""
        return f'\n\n<figure><img src="{src}" alt="{a.get("alt", "")}"{width}>{cap}</figure>\n\n'

    def gallery(_):
        ids = ",".join(str(i) for p, (i, _) in sorted(media.items()) if Path(p).suffix.lower() in IMAGE_EXT)
        return f'\n\n[gallery ids="{ids}"]\n\n'

    body = RE_REF.sub(ref, body)
    body = RE_FIGURE.sub(figure, body)
    body = RE_GALLERY.sub(gallery, body)
    # WP auto-embeds a bare YouTube URL on its own line
    body = RE_YOUTUBE.sub(r"\n\nhttps://www.youtube.com/watch?v=\1\n\n", body)
    for rel in sorted(media, key=len, reverse=True):
        body = re.sub(rf"(?<![\w/.-]){re.escape(rel)}(?![\w/.-])", media[rel][1], body)
    # CommonMark "\<" escape (Hugo honors it, python-markdown doesn't)
    body = body.replace("\\<", "&lt;")
    return markdown.markdown(body, extensions=["extra", "sane_lists"])


def map_terms(mapping, names):
    """Apply a hugo2wp_mapping.py mapping (unmapped names stay as is), dropping case-insensitive duplicates."""
    seen = {}
    for n in names or []:
        m = mapping.get(str(n), str(n))
        seen.setdefault(m.lower(), m)
    return list(seen.values())


class WP:
    def __init__(self, base, user, password):
        self.api = base.rstrip("/") + "/wp-json/wp/v2"
        self.s = requests.Session()
        self.s.auth = (user, password)
        self.names = {tax: self._all_terms(tax) for tax in ("categories", "tags")}
        self.terms = {tax: {n.lower(): i for n, i in names.items()} for tax, names in self.names.items()}

    def _req(self, method, path, **kw):
        r = self.s.request(method, f"{self.api}/{path}", timeout=120, **kw)
        if not r.ok:
            raise RuntimeError(f"{method} {path}: {r.status_code} {r.text[:300]}")
        return r

    def _all_terms(self, tax):
        terms, page = {}, 1
        while True:
            r = self._req("GET", tax, params={"per_page": 100, "page": page, "context": "edit"})
            # WP stores names HTML-escaped ("&amp;")
            terms.update({html.unescape(t["name"]): t["id"] for t in r.json()})
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                return terms
            page += 1

    def term_ids(self, tax, names):
        ids = []
        for name in names or []:
            key = str(name).lower()
            if key not in self.terms[tax]:
                self.terms[tax][key] = self._req("POST", tax, json={"name": str(name)}).json()["id"]
            ids.append(self.terms[tax][key])
        return ids

    def post_exists(self, slug):
        params = {"slug": slug, "status": "publish,draft,private,future,pending", "context": "edit"}
        return bool(self._req("GET", "posts", params=params).json())

    def upload(self, path):
        headers = {
            "Content-Disposition": f'attachment; filename="{path.name}"',
            "Content-Type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        }
        j = self._req("POST", "media", data=path.read_bytes(), headers=headers).json()
        return j["id"], j["source_url"]

    def create_post(self, data):
        return self._req("POST", "posts", json=data).json()


def main():
    p = ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("bundles", nargs="*", type=Path, help="bundle dirs to push (default: all under --content)")
    p.add_argument("--content", type=Path, default=Path("content/posts"))
    p.add_argument("--url", help="WordPress base URL, e.g. https://blog.example.com")
    p.add_argument("--include-draft", action="store_true", help="also push draft: true posts (as WP drafts)")
    p.add_argument("--dry-run", action="store_true", help="convert and print HTML, touch nothing")
    p.add_argument("--tag-mapping-file", type=Path, help="JSON from hugo2wp_mapping.py")
    args = p.parse_args()
    mapping = json.loads(args.tag_mapping_file.read_text()) if args.tag_mapping_file else {}

    indexes = sorted(args.content.glob("**/index.md"))
    urls = {}
    for idx in indexes:
        fm, _ = read_bundle(idx)
        urls[idx.parent.name] = url_of(idx.parent, fm)

    wp = None
    if not args.dry_run:
        if not args.url:
            p.error("--url is required unless --dry-run")
        wp = WP(args.url, os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])

    todo = [b / "index.md" for b in args.bundles] if args.bundles else indexes
    for idx in todo:
        fm, body = read_bundle(idx)
        bundle, slug = idx.parent, slug_of(idx.parent, fm)
        if fm.get("draft") and not args.include_draft:
            print(f"skip (draft) {slug}")
            continue
        status = "draft" if fm.get("draft") else "private" if fm.get("private") else "publish"
        files = sorted(f for f in bundle.rglob("*") if f.is_file() and f.name != "index.md")
        cats = map_terms(mapping.get("categories", {}), fm.get("categories"))
        tags = map_terms(mapping.get("tags", {}), fm.get("tags"))

        if args.dry_run:
            media = {str(f.relative_to(bundle)): (0, f"MEDIA/{f.name}") for f in files}
            print(f"== {slug} [{status}] {fm['title']}\ncategories={cats} tags={tags}")
            print(f"{convert(body, media, urls)}\n")
            continue
        assert wp
        if wp.post_exists(slug):
            print(f"skip (exists) {slug}")
            continue

        media = {str(f.relative_to(bundle)): wp.upload(f) for f in files}
        date = fm["date"]
        post = wp.create_post(
            {
                "title": fm["title"],
                "slug": slug,
                "status": status,
                "date_gmt": date.astimezone(timezone.utc).replace(tzinfo=None).isoformat(),
                "content": convert(body, media, urls),
                "categories": wp.term_ids("categories", cats),
                "tags": wp.term_ids("tags", tags),
            }
        )
        print(f"created {slug} -> {post['link']} ({len(media)} media)")


if __name__ == "__main__":
    main()
