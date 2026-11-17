#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4", "markdown", "markdownify", "pyyaml", "requests", "textual"]
# ///
"""TUI to edit which tags the WordPress posts carry ("email view": post list left, tags + Markdown right).

Posts tab: t / enter focus the post's tag list, there a adds (autocomplete), d / backspace / del
remove a tag, escape returns to the post list. a in the post list adds, too.
space marks posts, m edits all marked: "foo" adds foo, "-foo" removes it. f filters by tag,
escape in the post list clears the filter, another escape the marks. Changes stay pending (* in the list) until s saves all; u discards
those of the marked (else the selected) posts. Unknown tag names are created on save.
Posts are listed newest first, D marks drafts (any status but publish); c toggles a tags column,
o opens the post in the browser. / searches the full titles, n jumps to the next match.
Tags tab: tag -> number of posts (drafts included, trash ignored); / and n search tag names;
s switches sorting between name and post count, r reverses it (or click a header);
x deletes unused tags.

Tag changes create no WP revision, so each save appends post id, old and new tags to --log.
Env: WP_URL, WP_USER, WP_APP_PASSWORD (as for wp2hugo.py).
"""

import html
import json
import os
import sys
import unicodedata
import webbrowser
from argparse import ArgumentParser
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from hugo2wp_mapping import Prompt
from requests.adapters import HTTPAdapter
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Markdown
from textual.widgets import (DataTable, Footer, Label, OptionList,
                             TabbedContent, TabPane)
from urllib3.util import Retry
from wp2hugo import WP, Bundle, Media, convert


def edit(tags, op):
    """Tags after the mass-edit op: "foo" adds foo, "-foo" removes it. Order is kept."""
    if op.startswith("-"):
        name = op[1:].strip().lower()
        return [t for t in tags if t.lower() != name]
    return tags if op.lower() in (t.lower() for t in tags) else [*tags, op]


class TagWP(WP):
    """wp2hugo's REST client plus retries (unreachable host, 5xx) and the writes this tool needs."""

    def __init__(self, base, user, password):
        super().__init__(base, user, password)
        retry = Retry(
            total=6,
            backoff_factor=1,
            status_forcelist=(502, 503, 504),
            allowed_methods=None,
            raise_on_status=False,
        )
        self.s.mount("http://", HTTPAdapter(max_retries=retry))
        self.s.mount("https://", HTTPAdapter(max_retries=retry))

    def call(self, method, path, **kw):
        r = self.s.request(
            method, f"{self.base}/wp-json/wp/v2/{path}", timeout=120, **kw
        )
        return r, r.json() if r.content else None

    def create_tag(self, name):
        r, body = self.call("POST", "tags", json={"name": name})
        if r.ok:
            return body["id"]
        # e.g. a retried POST that did go through
        if body and body.get("code") == "term_exists":
            return body["data"]["term_id"]
        raise RuntimeError(f"create tag {name!r}: {r.status_code} {r.text[:200]}")

    def set_tags(self, post_id, ids):
        r, _ = self.call("POST", f"posts/{post_id}", json={"tags": ids})
        if not r.ok:
            raise RuntimeError(f"post {post_id}: {r.status_code} {r.text[:200]}")

    def delete_tag(self, tag_id):
        r, _ = self.call("DELETE", f"tags/{tag_id}", params={"force": "true"})
        if not r.ok:
            raise RuntimeError(f"delete tag {tag_id}: {r.status_code} {r.text[:200]}")


class MassPrompt(Prompt):
    """Prompt whose candidates ignore a leading "-" and keep it on the picked name."""

    def refilter(self, text):
        super().refilter(text.lstrip("-"))

    def sign(self):
        return "-" if self.query_one("Input").value.lstrip().startswith("-") else ""

    def action_complete(self, prefix=""):
        super().action_complete(self.sign())

    # prevent_default: Textual would also run Prompt's handler, dismissing twice
    def on_input_submitted(self, event):
        event.prevent_default()
        options = self.query_one(OptionList)
        if options.highlighted is not None:
            self.dismiss(
                self.sign()
                + str(options.get_option_at_index(options.highlighted).prompt)
            )
        else:
            self.dismiss(event.value.strip())

    def on_option_list_option_selected(self, event):
        event.prevent_default()
        self.dismiss(self.sign() + str(event.option.prompt))


class Confirm(ModalScreen[bool]):
    BINDINGS = [("y", "dismiss(True)", "Yes"), ("n,escape", "dismiss(False)", "No")]

    def __init__(self, question):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.question)
            yield Label("[b]y[/b]es / [b]n[/b]o")


class Info(ModalScreen[None]):
    BINDINGS = [("enter,escape,space", "dismiss", "OK")]

    def __init__(self, message):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(Text(self.message))
            yield Label("[b]enter[/b] to close")


class SearchTable(DataTable):
    BINDINGS = [
        ("slash", "app.search", "Search"),
        ("n", "app.search_next", "Next match"),
    ]


class PostTable(SearchTable):
    BINDINGS = [("a", "app.add_tag", "Add tag")]


class TagTable(SearchTable):
    # s shadows the app's save here; edits (and so saving) happen in the posts tab
    BINDINGS = [("s", "app.sort(-1)", "Sort by"), ("r", "app.sort_reverse", "Reverse")]


class TagList(OptionList):
    BINDINGS = [
        ("a", "app.add_tag", "Add tag"),
        ("d,backspace,delete", "app.remove_tag", "Remove tag"),
    ]

    def on_focus(self):
        if self.highlighted is None and self.option_count:
            self.highlighted = 0


class TagsApp(App):
    CSS = """
    TabbedContent, ContentSwitcher, TabPane { height: 1fr; }
    #posts { width: 1fr; max-width: 50%; }
    #posts.narrow { width: auto; }
    #side { width: 1fr; }
    #tags { height: auto; max-height: 12; border: round $primary; }
    #tags:focus { border: round $accent; }
    ModalScreen { align: center middle; }
    .dialog { width: 70; height: auto; border: thick $primary; background: $surface; padding: 1 2; }
    .dialog OptionList { height: auto; max-height: 15; }
    """
    BINDINGS = [
        ("1", "tab('posts-tab')", "Posts"),
        ("2", "tab('tags-tab')", "Tags"),
        ("t", "focus('tags')", "Tag list"),
        ("c", "toggle_tags", "Tags column"),
        ("o", "open", "Open"),
        ("space", "mark", "Mark"),
        ("m", "mass", "Edit marked"),
        ("f", "filter", "Filter"),
        ("escape", "reset", "Reset"),
        ("s", "save", "Save"),
        ("u", "discard", "Discard"),
        ("x", "delete_unused", "Delete unused"),
        ("q", "request_quit", "Quit"),
    ]

    def __init__(self, wp, posts, tag_ids, log):
        super().__init__()
        self.wp, self.posts, self.tag_ids, self.changelog = (
            wp,
            {p["id"]: p for p in posts},
            tag_ids,
            log,
        )
        self.host = urlparse(wp.base).netloc
        self.pending, self.marked, self.tag_filter = {}, set(), None
        self.tag_sort = (1, True)  # (column, reverse): post count, largest first
        self.tag_column = False
        self.search_text = {"posts": "", "tagtable": ""}  # by table id

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="posts-tab"):
            with TabPane("Posts", id="posts-tab"):
                with Horizontal():
                    yield PostTable(id="posts", cursor_type="row", zebra_stripes=True)
                    with Vertical(id="side"):
                        yield TagList(id="tags")
                        with VerticalScroll():
                            yield Markdown(id="body")
            with TabPane("Tags", id="tags-tab"):
                yield TagTable(id="tagtable", cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self):
        tagtable = self.query_one("#tagtable", DataTable)
        tagtable.add_column("Tag", key="tag")
        tagtable.add_column("Posts", key="count")
        self.refresh_posts()
        self.query_one("#posts", DataTable).focus()

    def tags_of(self, pid):
        return self.pending.get(pid, self.posts[pid]["tags"])

    def set_tags(self, pid, tags):
        if tags == self.posts[pid]["tags"]:
            self.pending.pop(pid, None)
        else:
            self.pending[pid] = tags

    def counts(self):
        counts = Counter({name: 0 for name in self.tag_ids})
        for pid in self.posts:
            counts.update(self.tags_of(pid))
        return counts

    def row(self, pid):
        """Cells by column key; Text, as a str cell would be parsed as Rich markup ("[draft]")."""
        p = self.posts[pid]
        flag = "".join(
            c if on else " "
            for c, on in (
                ("D", p["status"] != "publish"),
                ("*", pid in self.pending),
                ("+", pid in self.marked),
            )
        )
        cells = {"flag": flag, "date": p["date"][:10], "title": p["title"]}
        if self.tag_column:
            cells["tags"] = ", ".join(self.tags_of(pid))
        return {k: Text(v) for k, v in cells.items()}

    def searched(self):
        """(table, full text of a row key): post title, or the tag name the tag rows are keyed by."""
        if self.query_one(TabbedContent).active == "posts-tab":
            return self.query_one("#posts", DataTable), lambda k: self.posts[int(k)][
                "title"
            ]
        return self.query_one("#tagtable", DataTable), lambda k: k

    def action_search(self):
        table, _ = self.searched()

        def done(text):
            if text:
                self.search_text[table.id] = text
                self.action_search_next()

        what = "post titles" if table.id == "posts" else "tags"
        self.push_screen(
            Prompt(f"Search {what}:", self.search_text[table.id], []), done
        )

    def action_search_next(self):
        """Next row (after the cursor, wrapping) whose full text contains the table's search text."""
        table, text_of = self.searched()
        wanted = self.search_text[table.id].lower()
        if not wanted or not table.row_count:
            return
        keys = [row.key.value for row in table.ordered_rows]
        start = table.cursor_row + 1
        for i in range(len(keys)):
            row = (start + i) % len(keys)
            if wanted in text_of(keys[row]).lower():
                table.move_cursor(row=row)
                return
        self.notify(f"no match for {self.search_text[table.id]!r}", severity="warning")

    def action_open(self):
        pid = self.current()
        if pid is not None:
            webbrowser.open(self.posts[pid]["link"])

    def action_toggle_tags(self):
        self.tag_column = not self.tag_column
        self.refresh_posts()

    def refresh_posts(self):
        """Rebuild both tables, keeping the post cursor where possible."""
        table = self.query_one("#posts", DataTable)
        current = self.current()
        table.clear(columns=True)
        table.add_column("", key="flag")
        table.add_column("Date", key="date")
        table.add_column("Title", key="title", width=45)
        table.set_class(not self.tag_column, "narrow")
        if self.tag_column:
            table.add_column("Tags", key="tags")
        wanted = (self.tag_filter or "").lower()
        for pid in sorted(
            self.posts, key=lambda i: self.posts[i]["date"], reverse=True
        ):
            if not wanted or wanted in (t.lower() for t in self.tags_of(pid)):
                table.add_row(*self.row(pid).values(), key=str(pid))
        if current is not None and str(current) in table.rows:
            table.move_cursor(row=table.get_row_index(str(current)))
        self.sub_title = f"filter: {self.tag_filter}" if self.tag_filter else ""
        tagtable = self.query_one("#tagtable", DataTable)
        tagtable.clear()
        for name, n in self.counts().items():
            tagtable.add_row(Text(name), n, key=name)
        self.sort_tags()
        self.show(self.current())

    def sort_tags(self):
        col, reverse = self.tag_sort

        def name(r):  # NFKD sorts umlauts with their base letter
            return unicodedata.normalize("NFKD", str(r[0])).casefold()

        key = name if col == 0 else (lambda r: (r[1], name(r)))
        self.query_one("#tagtable", DataTable).sort(key=key, reverse=reverse)

    def action_sort(self, col):
        """Sort by column col (-1: the other one); same column again flips, counts start largest first."""
        last_col, last_reverse = self.tag_sort
        col = 1 - last_col if col < 0 else col
        self.tag_sort = (col, not last_reverse if col == last_col else col == 1)
        self.sort_tags()

    def action_sort_reverse(self):
        self.action_sort(self.tag_sort[0])

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected):
        if event.data_table.id == "tagtable":
            self.action_sort(event.column_index)

    def update_rows(self, pids):
        table = self.query_one("#posts", DataTable)
        for pid in pids:
            if str(pid) in table.rows:
                for key, value in self.row(pid).items():
                    table.update_cell(str(pid), key, value, update_width=key == "tags")
        self.show(self.current())

    def current(self):
        table = self.query_one("#posts", DataTable)
        if not table.row_count:
            return None
        return int(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)

    def show(self, pid):
        taglist = self.query_one(TagList)
        highlighted = taglist.highlighted
        taglist.clear_options()
        if pid is None:
            self.query_one(Markdown).update("")
            return
        taglist.add_options(Text(t) for t in self.tags_of(pid))
        if highlighted is not None and taglist.option_count:
            taglist.highlighted = min(highlighted, taglist.option_count - 1)
        p = self.posts[pid]
        if "md" not in p:
            # empty Media: images keep their WP URLs, which is fine for a preview
            p["md"] = convert(p["html"], self.host, Bundle(Media([])), lambda msg: None)
        self.query_one(Markdown).update(f"# {p['title']}\n\n{p['md']}")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.data_table.id == "posts" and event.row_key.value:
            self.show(int(event.row_key.value))

    def candidates(self):
        names = {*self.tag_ids, *(t for tags in self.pending.values() for t in tags)}
        return sorted(names, key=str.lower)

    def canonical(self, name):
        """Existing spelling of name (WP tag names are unique case-insensitively)."""
        return next((c for c in self.candidates() if c.lower() == name.lower()), name)

    def action_add_tag(self):
        pid = self.current()
        if pid is None:
            return

        def done(name):
            if name:
                self.set_tags(pid, edit(self.tags_of(pid), self.canonical(name)))
                self.update_rows([pid])

        self.push_screen(
            Prompt(f"Add tag to '{self.posts[pid]['title']}':", "", self.candidates()),
            done,
        )

    def action_remove_tag(self):
        pid, taglist = self.current(), self.query_one(TagList)
        if pid is not None and taglist.highlighted is not None:
            self.set_tags(
                pid,
                edit(self.tags_of(pid), "-" + self.tags_of(pid)[taglist.highlighted]),
            )
            self.update_rows([pid])

    def action_mark(self):
        pid = self.current()
        if pid is not None:
            self.marked ^= {pid}
            self.update_rows([pid])
            self.query_one("#posts", DataTable).action_cursor_down()

    def action_mass(self):
        if not self.marked:
            self.notify("No posts marked (space)", severity="warning")
            return

        def done(op):
            if op and op.lstrip("-").strip():
                sign, name = ("-", op[1:].strip()) if op.startswith("-") else ("", op)
                for pid in self.marked:
                    self.set_tags(
                        pid, edit(self.tags_of(pid), sign + self.canonical(name))
                    )
                self.update_rows(self.marked)

        question = f"Tag for {len(self.marked)} marked posts (foo adds, -foo removes):"
        self.push_screen(MassPrompt(question, "", self.candidates()), done)

    def action_filter(self):
        def done(name):
            if name:
                self.tag_filter = self.canonical(name)
                self.refresh_posts()

        used = [name for name, n in self.counts().items() if n]
        self.push_screen(
            Prompt("Show posts tagged:", "", sorted(used, key=str.lower)), done
        )

    def action_reset(self):
        """Escape, one step each: tag list -> post list, then clear the filter, then the marks."""
        if isinstance(self.focused, TagList):
            self.query_one("#posts", DataTable).focus()
        elif self.tag_filter:
            self.tag_filter = None
            self.refresh_posts()
        elif self.marked:
            # update_rows, not refresh_posts: a rebuild scrolls back to the cursor
            marked, self.marked = self.marked, set()
            self.update_rows(marked)

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id == "posts":
            self.query_one(TagList).focus()

    def action_discard(self):
        pids = self.marked or {self.current()} - {None}
        for pid in pids:
            self.pending.pop(pid, None)
        self.update_rows(pids)

    def action_tab(self, tab):
        self.query_one(TabbedContent).active = tab
        self.query_one(
            "#posts" if tab == "posts-tab" else "#tagtable", DataTable
        ).focus()

    def action_save(self):
        # ponytail: synchronous, UI blocks while saving; a worker thread if mass saves get slow
        saved, failed = [], 0
        with self.changelog.open("a") as log:
            for pid, tags in list(self.pending.items()):
                try:
                    for name in tags:
                        if name not in self.tag_ids:
                            self.tag_ids[name] = self.wp.create_tag(name)
                    self.wp.set_tags(pid, [self.tag_ids[t] for t in tags])
                except Exception as e:  # noqa: BLE001 -- keep the post pending, report, go on
                    failed += 1
                    self.notify(str(e), severity="error", timeout=10)
                    continue
                entry = {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "post": pid,
                }
                log.write(
                    json.dumps(
                        {**entry, "old": self.posts[pid]["tags"], "new": tags},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                self.posts[pid]["tags"] = tags
                del self.pending[pid]
                saved.append(pid)
        self.refresh_posts()
        posts = f"{len(saved)} post{'' if len(saved) == 1 else 's'}"
        if failed:
            message = f"Saved {posts}, {failed} FAILED (still pending, see errors)."
        else:
            message = f"All saved ({posts})." if saved else "Nothing to save."
        self.push_screen(Info(message))

    def action_delete_unused(self):
        if self.pending:
            self.notify("Save or discard pending changes first", severity="warning")
            return
        unused = sorted(
            (name for name, n in self.counts().items() if not n), key=str.lower
        )
        if not unused:
            self.notify("No unused tags")
            return

        def done(yes):
            if not yes:
                return
            for name in unused:
                try:
                    self.wp.delete_tag(self.tag_ids.pop(name))
                except Exception as e:  # noqa: BLE001
                    self.notify(str(e), severity="error", timeout=10)
            self.refresh_posts()

        names = ", ".join(unused)
        self.push_screen(
            Confirm(f"Delete {len(unused)} unused tags from WordPress?\n\n{names}"),
            done,
        )

    def action_request_quit(self):
        if not self.pending:
            self.exit()
            return
        question = f"{len(self.pending)} posts have unsaved changes. Quit anyway?"
        self.push_screen(Confirm(question), lambda yes: self.exit() if yes else None)


def load(wp):
    tags = {
        t["id"]: html.unescape(t["name"]) for t in wp.all("tags", _fields="id,name")
    }
    fields = "id,date,status,link,title,tags,content"
    posts = [
        {
            "id": p["id"],
            "date": p["date"],
            "status": p["status"],
            "title": html.unescape(p["title"]["raw"] or p["title"]["rendered"])
            or "(no title)",
            "tags": [tags[i] for i in p["tags"] if i in tags],
            "link": p["link"],
            "html": p["content"]["rendered"],
        }
        for p in wp.all("posts", status="any", context="edit", _fields=fields)
    ]
    return posts, {name: tid for tid, name in tags.items()}


def main():
    p = ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument(
        "--url",
        default=os.environ.get("WP_URL"),
        help="WordPress base URL (default: $WP_URL)",
    )
    p.add_argument(
        "--log",
        type=Path,
        default=Path("wp_tags.jsonl"),
        help="change log, appended to",
    )
    args = p.parse_args()
    if not args.url:
        p.error("--url or WP_URL is required")
    wp = TagWP(args.url, os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])
    print(f"loading posts from {wp.base} ...", file=sys.stderr)
    posts, tag_ids = load(wp)
    TagsApp(wp, posts, tag_ids, args.log).run()


if __name__ == "__main__":
    main()
