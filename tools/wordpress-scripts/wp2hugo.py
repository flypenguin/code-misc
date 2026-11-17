#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4", "markdownify", "pyyaml", "requests"]
# ///
"""Mirror a WordPress site (posts, pages, media) into a Hugo tree via the REST API.

Auth (optional): WordPress application password passed as WP_USER / WP_APP_PASSWORD
env vars. Without it only public content is mirrored; with it drafts etc. as well.

Layout under --out: content/posts/<YYYY>/<YYYY-MM-DD-HHMM>-<slug>/index.md, pages at
content/<link path>/index.md, images used by a page next to it, all other media in
static/images/<YYYY>/<MM>/. Re-runnable: downloads are kept while their size matches WP's, files this run
did not produce are deleted from content/ and static/images/. Pages that only hold
listing blocks (tag cloud, archives, ...) are skipped; that needs auth to see raw content.
"""

import html
import os
import re
import sys
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
import yaml
from bs4 import BeautifulSoup, NavigableString
from markdownify import ATX, MarkdownConverter, chomp

RE_WPIMAGE = re.compile(r"wp-image-(\d+)")
RE_CLASS = re.compile(r"align(left|right|center|wide|full)|is-style-.+")
RE_COLUMNS = re.compile(r"columns-(\d+)")
RE_YT_URL = re.compile(r"(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)([\w-]+)")
RE_YT_TEXT = re.compile(r"\[youtube\s+([^\]\s]+)\]")
RE_UPLOAD = re.compile(r"wp-content/uploads/(\d{4})/(\d{2})/")
# undo wptexturize: typographic quotes and ellipsis -> ASCII; nbsp -> space. Dashes, emoji stay.
ASCII_PUNCT = {
    **dict.fromkeys((0x201C, 0x201D, 0x201E, 0x201F, 0xAB, 0xBB, 0x2033), '"'),
    **dict.fromkeys((0x2018, 0x2019, 0x201A, 0x201B, 0x2039, 0x203A, 0x2032), "'"),
    0x2026: "...",
    0xA0: " ",
}
# server-rendered listing blocks; the static site generator builds these itself
RE_LISTING = re.compile(r"<!-- wp:(?:tag-cloud|archives|categories|latest-posts|page-list|calendar)\b[^>]*/-->")


def generated(item):
    """True if the raw content is nothing but listing blocks (needs context=edit)."""
    raw = (item["content"].get("raw") or "").strip()
    return bool(raw) and not RE_LISTING.sub("", raw).strip()


class Ts(str):
    """Timestamp emitted as a plain (unquoted) YAML scalar."""


class Dumper(yaml.SafeDumper):
    pass


Dumper.add_representer(Ts, lambda d, v: d.represent_scalar("tag:yaml.org,2002:timestamp", str(v)))


def warn_stderr(msg):
    print(f"WARN: {msg}", file=sys.stderr)


class Media:
    """All media items, indexed by id and by every known file URL (source + size variants)."""

    def __init__(self, items):
        self.by_id = {m["id"]: m for m in items}
        self.by_url, self.size_by_url = {}, {}
        for m in items:
            details = m.get("media_details")
            sizes = details.get("sizes", {}) if isinstance(details, dict) else {}
            if isinstance(details, dict) and isinstance(details.get("filesize"), int):
                self.size_by_url[m["source_url"]] = details["filesize"]
            for url in [m["source_url"], *(s["source_url"] for s in sizes.values())]:
                self.by_url.setdefault(url, m["id"])


class Bundle:
    """Files one page bundle needs: media id -> bundle filename."""

    def __init__(self, media):
        self.media = media
        self.names = {}
        self.files = {}

    def add(self, mid):
        if mid not in self.names:
            url = self.media.by_id[mid]["source_url"]
            name = unquote(Path(urlparse(url).path).name)
            if name in self.files:
                name = f"{mid}-{name}"
            self.names[mid] = name
            self.files[name] = url
        return self.names[mid]


def esc(value):
    return " ".join(str(value).split()).replace("\\", "\\\\").replace('"', '\\"')


def yt_id(s):
    m = RE_YT_URL.search(s) or re.search(r"[?&]v=([\w-]+)", s)
    return m[1] if m else s


class Converter(MarkdownConverter):
    """WP rendered HTML -> Markdown with numbered reference links and Hugo shortcodes."""

    def __init__(self, host, bundle, warn=warn_stderr):
        super().__init__(heading_style=ATX, bullets="-")
        self.host, self.bundle, self.media, self.warn = host, bundle, bundle.media, warn
        self.refs = {}

    def rewrite(self, href):
        mid = self.media.by_url.get(href)
        if mid:
            return self.bundle.add(mid)
        u = urlparse(href)
        if u.netloc == self.host:
            return u._replace(scheme="", netloc="").geturl() or "/"
        return href

    def media_id(self, img):
        for c in img.get("class", []):
            m = RE_WPIMAGE.fullmatch(c)
            if m and int(m[1]) in self.media.by_id:
                return int(m[1])
        return self.media.by_url.get(img.get("src"))

    def figure(self, img, stop, caption=""):
        """Figure shortcode for img; classes come from img up to the ancestor `stop`."""
        src = img.get("src", "")
        mid = self.media_id(img)
        if mid:
            src = self.bundle.add(mid)
        else:
            self.warn(f"unresolved image {src}")
        wrap = img.parent if img.parent.name == "a" else None
        classes = list(img.get("class", []))
        for p in [] if stop is img else img.parents:
            classes += p.get("class", [])
            if p is stop:
                break
        classes = dict.fromkeys(c for c in classes if RE_CLASS.fullmatch(c))
        width = img.get("width", "")
        params = {
            "src": src,
            "alt": img.get("alt", ""),
            "caption": caption,
            "class": " ".join(classes),
            "width": width if width.isdigit() else "",
            "link": self.rewrite(wrap["href"]) if wrap and wrap.get("href") else "",
        }
        return "{{< figure " + " ".join(f'{k}="{esc(v)}"' for k, v in params.items() if v) + " >}}"

    def raw(self, soup, text, block=True):
        tag = soup.new_tag("wpraw")
        tag["v"], tag["block"] = text, "1" if block else ""
        return tag

    def convert_wpraw(self, el, text, parent_tags):
        return f"\n\n{el['v']}\n\n" if el["block"] else el["v"]

    def convert_a(self, el, text, parent_tags):
        prefix, suffix, text = chomp(text)
        if not text or not el.get("href"):
            return prefix + text + suffix
        n = self.refs.setdefault(self.rewrite(el["href"]), len(self.refs) + 1)
        return f"{prefix}[{text}][{n}]{suffix}"

    def prepare(self, soup):
        """Replace images, galleries and embeds by opaque <wpraw> nodes holding shortcodes."""

        def txt(el):
            return " ".join(el.get_text().split()) if el else ""

        for g in soup.select("figure.wp-block-gallery, ul.wp-block-gallery, div.wp-block-gallery, div.gallery"):
            cols = RE_COLUMNS.search(" ".join(g.get("class", [])))
            items = []
            for img in g.find_all("img"):
                cap = ""
                for p in img.parents:
                    if p is g:
                        break
                    if p.name in ("figure", "dl", "li"):
                        cap = txt(p.find("figcaption") or p.select_one(".gallery-caption, .wp-caption-text"))
                        break
                items.append(self.figure(img, g, cap))
            body = "\n".join(items)
            open_tag = f'{{{{< gallery columns="{cols[1] if cols else 3}" >}}}}'
            g.replace_with(self.raw(soup, f"{open_tag}\n{body}\n{{{{< /gallery >}}}}"))

        for f in soup.select("figure, div.wp-caption"):
            imgs = f.find_all("img")
            if len(imgs) == 1:
                cap = txt(f.find("figcaption") or f.select_one(".wp-caption-text"))
                f.replace_with(self.raw(soup, self.figure(imgs[0], f, cap)))

        for img in soup.find_all("img"):
            if "wp-smiley" in img.get("class", []):
                img.replace_with(NavigableString(img.get("alt", "")))
                continue
            wrap = img.parent
            if wrap.name != "a" or len(wrap.find_all(True)) > 1 or wrap.get_text(strip=True):
                wrap = img
            wrap.replace_with(self.raw(soup, self.figure(img, img)))

        for f in soup.find_all("iframe"):
            m = RE_YT_URL.search(f.get("src", ""))
            if m:
                f.replace_with(self.raw(soup, f"{{{{< youtube {m[1]} >}}}}"))
            else:
                self.warn(f"dropped iframe {f.get('src')}")

        for node in soup.find_all(string=RE_YT_TEXT):
            parts = RE_YT_TEXT.split(str(node))
            new = [
                NavigableString(s) if i % 2 == 0 else self.raw(soup, f"{{{{< youtube {yt_id(s)} >}}}}")
                for i, s in enumerate(parts)
            ]
            node.replace_with(*new)

    def run(self, rendered):
        soup = BeautifulSoup(rendered, "html.parser")
        for s in soup.find_all(string=True):
            s.replace_with(s.translate(ASCII_PUNCT))
        for tag in soup.find_all(True):
            tag.attrs = {k: v.translate(ASCII_PUNCT) if isinstance(v, str) else v for k, v in tag.attrs.items()}
        self.prepare(soup)
        out = self.convert_soup(soup).strip()
        defs = "\n".join(f"[{n}]: {u.replace(' ', '%20')}" for u, n in self.refs.items())
        return out + ("\n\n" + defs if defs else "") + "\n"


def convert(rendered, host, bundle, warn=warn_stderr):
    return Converter(host, bundle, warn).run(rendered)


def slug_of(item):
    return item.get("slug") or item.get("generated_slug") or str(item["id"])


def post_dir(post):
    d = post["date"]
    return Path("content/posts") / d[:4] / f"{d[:10]}-{d[11:13]}{d[14:16]}-{slug_of(post)}"


def page_dir(page):
    path = urlparse(page["link"]).path.strip("/")
    if not path and page.get("permalink_template"):
        path = urlparse(page["permalink_template"]).path.strip("/").replace("%pagename%", slug_of(page))
    return Path("content") / (path or str(page["id"]))


def ts(gmt, local):
    return Ts((gmt or local)[:19] + "+00:00")


def front_matter(item, bundle, cats, tags, users):
    published = item["status"] == "publish"
    fm = {
        "title": html.unescape(item["title"]["rendered"]).translate(ASCII_PUNCT),
        "date": ts(item["date_gmt"], item["date"]),
        "slug": slug_of(item),
    }
    if published:
        fm["url"] = urlparse(item["link"]).path
    fm["categories"] = [cats.get(i, str(i)) for i in item.get("categories", [])]
    fm["tags"] = [tags.get(i, str(i)) for i in item.get("tags", [])]
    fm["author"] = users.get(item["author"], item["author"])
    if not published:
        fm["draft"] = True
    fm["wp_id"] = item["id"]
    if item.get("featured_media") in bundle.media.by_id:
        fm["featured_image"] = bundle.add(item["featured_media"])
    if (item.get("excerpt") or {}).get("raw"):
        fm["excerpt"] = item["excerpt"]["raw"].translate(ASCII_PUNCT)
    return fm


def render(fm, body):
    head = yaml.dump(fm, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=10**6)
    return f"---\n{head}---\n\n{body}"


class WP:
    def __init__(self, base, user=None, password=None):
        self.base = base.rstrip("/")
        self.s = requests.Session()
        self.authed = bool(user and password)
        if self.authed:
            self.s.auth = (user, password)

    def all(self, path, **params):
        items, page = [], 1
        while True:
            url = f"{self.base}/wp-json/wp/v2/{path}"
            r = self.s.get(url, params={"per_page": 100, "page": page, **params}, timeout=120)
            if not r.ok:
                raise RuntimeError(f"GET {path}: {r.status_code} {r.text[:300]}")
            items += r.json()
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                return items
            page += 1

    def content(self, path):
        extra = {"status": "any", "context": "edit"} if self.authed else {}
        return sorted(self.all(path, **extra), key=lambda i: i["id"])

    def users(self):
        try:
            return {u["id"]: u["name"] for u in self.all("users")}
        except RuntimeError:
            return {}


def stale(dest, size):
    """Missing, or its size differs from WP's media_details.filesize (if WP reports one)."""
    return not dest.exists() or (size is not None and dest.stat().st_size != size)


def download(job):
    dest, url = job
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        part = dest.with_name(dest.name + ".part")
        part.write_bytes(r.content)
        part.replace(dest)
        return dest, None
    except (requests.RequestException, OSError) as e:
        return dest, f"download {url}: {e}"


def prune(out, produced):
    for root in (out / "content", out / "static/images"):
        for f in root.rglob("*"):
            if f.is_file() and f not in produced:
                f.unlink()
        for d in sorted((d for d in root.rglob("*") if d.is_dir()), key=lambda d: len(d.parts), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()


def main():
    p = ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("--url", default=os.environ.get("WP_URL"), help="WordPress base URL (default: $WP_URL)")
    p.add_argument("--out", type=Path, required=True, help="output root")
    args = p.parse_args()
    if not args.url:
        p.error("--url or WP_URL is required")
    out = args.out
    warnings = []

    def warn(msg):
        warnings.append(msg)
        warn_stderr(msg)

    wp = WP(args.url, os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD"))
    host = urlparse(wp.base).netloc
    media = Media(wp.all("media", _fields="id,source_url,media_details"))
    cats = {c["id"]: html.unescape(c["name"]) for c in wp.all("categories")}
    tags = {t["id"]: html.unescape(t["name"]) for t in wp.all("tags")}
    users = wp.users()
    posts = [i for i in wp.content("posts") if not generated(i)]
    pages = [i for i in wp.content("pages") if not generated(i)]

    produced, jobs, placed = set(), {}, set()
    for item, rel in [(i, post_dir(i)) for i in posts] + [(i, page_dir(i)) for i in pages]:
        bundle = Bundle(media)
        slug = slug_of(item)
        body = convert(item["content"]["rendered"], host, bundle, lambda m, s=slug: warn(f"{s}: {m}"))
        index = out / rel / "index.md"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(render(front_matter(item, bundle, cats, tags, users), body))
        produced.add(index)
        placed |= bundle.names.keys()
        for name, url in bundle.files.items():
            jobs[out / rel / name] = url

    for mid in sorted(media.by_id.keys() - placed):
        url = media.by_id[mid]["source_url"]
        m = RE_UPLOAD.search(url)
        sub = Path(m[1]) / m[2] if m else Path()
        jobs[out / "static/images" / sub / unquote(Path(urlparse(url).path).name)] = url

    todo = [(d, u) for d, u in sorted(jobs.items()) if stale(d, media.size_by_url.get(u))]
    for d, _ in todo:
        d.parent.mkdir(parents=True, exist_ok=True)
    failed = set()
    with ThreadPoolExecutor(max_workers=8) as ex:
        for dest, err in ex.map(download, todo):
            if err:
                failed.add(dest)
                warn(err)
    produced |= jobs.keys() - failed
    prune(out, produced)
    print(
        f"posts={len(posts)} pages={len(pages)} media={len(media.by_id)} "
        f"files={len(jobs)} downloaded={len(todo) - len(failed)} warnings={len(warnings)}"
    )


if __name__ == "__main__":
    main()
