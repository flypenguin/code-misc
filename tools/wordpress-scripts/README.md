# wordpress-scripts

Helpers to mirror a WordPress site into Hugo, push Hugo posts into WordPress, and clean up
WordPress content via its REST API. A local WordPress to test against:
[wp-compose](../../compose-stacks/wp-compose/).

All Python scripts need [uv](https://docs.astral.sh/uv/); dependencies are declared inline, so
`./<script>.py` just works. Auth for all of them: `WP_USER` plus `WP_APP_PASSWORD`, a WordPress
application password (Users > Profile > Application Passwords). Most take the site from `WP_URL`
or `--url`.

The standalone scripts (`wp2hugo.py`, `wp_lightbox.py`, `hugo2wp.py`) also run straight from
GitHub, e.g.:

```sh
uv run https://raw.githubusercontent.com/flypenguin/code-misc/main/tools/wordpress-scripts/wp2hugo.py --out <dir>
```

`hugo2wp_mapping.py` and `wp_tags.py` import their siblings, so run them from a checkout.

## wp2hugo.py

Mirrors a WordPress site (posts, pages, media) into a Hugo tree.

```sh
WP_URL=https://example.org WP_USER=... WP_APP_PASSWORD=... ./wp2hugo.py --out <dir>
```

- `--out` (required) is the output root, `--url` overrides `WP_URL`.
- Without `WP_USER` / `WP_APP_PASSWORD` only public content is mirrored, and listing pages are
  not detected (see below).
- Layout under `--out`: `content/posts/<YYYY>/<YYYY-MM-DD-HHMM>-<slug>/index.md` per post with
  its images next to it, pages at `content/<page path>/index.md`, all other media in
  `static/images/<YYYY>/<MM>/`.
- Front matter: title, date, slug, url (the WordPress permalink path), categories, tags, author,
  draft (for anything not published), wp_id, featured_image, excerpt. No `lastmod`: WordPress
  bumps it on no-op saves.
- Body: HTML converted to Markdown. Links become numbered reference links, links to the site
  itself become paths. Images become `{{< figure >}}`, galleries `{{< gallery >}}`, YouTube
  embeds `{{< youtube >}}`. Images are always the full-size file.
- Typographic quotes and ellipses become ASCII, non-breaking spaces normal spaces. Dashes and
  emoji stay.
- Pages that consist only of listing blocks (tag cloud, archives, latest posts, ...) are skipped.
- Re-runnable and deterministic: same content, byte-identical output. Images are downloaded
  again only when missing or when their size differs. Files that no longer exist in WordPress
  are deleted from `content/` and `static/images/`.

## hugo2wp.py

Pushes Hugo page bundles (`content/posts/**/index.md`) into WordPress. A post whose slug already
exists is skipped, so it is re-runnable.

```sh
WP_USER=... WP_APP_PASSWORD=... ./hugo2wp.py --url https://example.org [--content content/posts] [bundle ...]
```

- `--dry-run` converts and prints HTML without `--url`, `--include-draft` also pushes drafts.
- `--tag-mapping-file` takes the JSON written by `hugo2wp_mapping.py`.
- Internal `{{< relref >}}` links point at the Hugo URL path, so set WP permalinks to
  `/%year%/%monthnum%/%day%/%postname%/`.

## hugo2wp_mapping.py

TUI to map Hugo tags and categories to WordPress names, writes the file for
`hugo2wp.py --tag-mapping-file`.

```sh
WP_USER=... WP_APP_PASSWORD=... ./hugo2wp_mapping.py --url https://example.org [--content content/posts] mapping.json
```

## wp_tags.py

TUI to edit which tags the WordPress posts carry: post list left, tags and Markdown right, mass
edits on marked posts, a tab with tag usage counts and deletion of unused tags. Keys: see the
module docstring.

```sh
WP_URL=https://example.org WP_USER=... WP_APP_PASSWORD=... ./wp_tags.py [--log wp_tags.jsonl]
```

Tag changes create no WordPress revision, so every save appends post id, old and new tags to
`--log`.

## wp_lightbox.py

Sets "Link to > Enlarge on click" (lightbox) on every gallery and image block, like the block
editor does. Classic `[gallery]` shortcodes and bare `<img>` are only reported.

```sh
WP_URL=https://example.org WP_USER=... WP_APP_PASSWORD=... ./wp_lightbox.py [--apply]
```

Dry run by default, `--apply` writes. Have a database backup: posts that never had a revision
cannot be rolled back.

## wp_classic_to_blocks.js

Converts every classic-editor post and page to blocks, run from the browser console. See
[wp_classic_to_blocks.md](wp_classic_to_blocks.md).

## Tests

No network needed. From this directory:

```sh
uv run --no-project --with pytest --with beautifulsoup4 --with markdown --with markdownify --with pyyaml --with requests --with textual pytest -q
```
