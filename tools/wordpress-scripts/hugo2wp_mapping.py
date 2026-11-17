#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown", "pyyaml", "requests", "textual"]
# ///
"""TUI to map Hugo tags/categories to WordPress names, for hugo2wp.py --tag-mapping-file.

Enter edits the selected row; an empty value removes the mapping (name is kept as is).
n / p (or a header click) sort by name / post count, again to reverse.
The edit dialog filters candidates while typing: the WordPress site's existing terms plus
names already mapped to (new terms the uploader will create). Tab completes the last one left.
"""

import json
import os
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path

from hugo2wp import WP, read_bundle
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (Button, DataTable, Footer, Input, Label,
                             OptionList, TabbedContent, TabPane)

TAXONOMIES = ("tags", "categories")


class Prompt(ModalScreen[str | None]):
    """Input plus a filtered candidate list: up/down picks, Enter takes the pick or else the typed text."""

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancel"),
        ("down", "move('down')", "Next"),
        ("up", "move('up')", "Previous"),
        ("tab", "complete", "Complete"),
    ]

    def __init__(self, question, value, candidates):
        super().__init__()
        self.question, self.value, self.candidates = question, value, candidates

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.question)
            yield Input(self.value)
            yield OptionList()

    def on_mount(self):
        self.query_one(Input).focus()
        self.refilter("")

    def on_input_changed(self, event: Input.Changed):
        self.refilter(event.value)

    def refilter(self, text):
        options = self.query_one(OptionList).clear_options()
        options.add_options(
            c for c in self.candidates if text.strip().lower() in c.lower()
        )
        options.highlighted = None

    def action_complete(self, prefix=""):
        """Tab: put the only remaining candidate into the input."""
        options = self.query_one(OptionList)
        if options.option_count == 1:
            field = self.query_one(Input)
            field.value = prefix + str(options.get_option_at_index(0).prompt)
            field.cursor_position = len(field.value)

    def action_move(self, direction):
        getattr(self.query_one(OptionList), f"action_cursor_{direction}")()

    def on_input_submitted(self, event: Input.Submitted):
        options = self.query_one(OptionList)
        if options.highlighted is not None:
            self.dismiss(str(options.get_option_at_index(options.highlighted).prompt))
        else:
            self.dismiss(event.value.strip())

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        self.dismiss(str(event.option.prompt))


class SavePrompt(ModalScreen[str | bool | None]):
    """Dismisses with a path (save), False (quit without saving) or None (cancel)."""

    BINDINGS = [("escape", "dismiss(None)", "Cancel")]

    def __init__(self, path):
        super().__init__()
        self.path = path

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Save mappings to:")
            yield Input(self.path)
            with Horizontal():
                yield Button("Save", variant="primary", id="save")
                yield Button("Don't save", variant="error", id="discard")
                yield Button("Cancel", id="cancel")

    def on_input_submitted(self, event: Input.Submitted):
        self.dismiss(event.value.strip())

    def on_button_pressed(self, event: Button.Pressed):
        result = {"save": self.query_one(Input).value.strip(), "discard": False}
        self.dismiss(result.get(event.button.id or ""))


class MappingApp(App):
    CSS = """
    TabbedContent, ContentSwitcher, TabPane, DataTable { height: 1fr; }
    ModalScreen { align: center middle; }
    .dialog { width: 70; height: auto; border: thick $primary; background: $surface; padding: 1 2; }
    .dialog Horizontal { height: auto; margin-top: 1; }
    .dialog OptionList { height: auto; max-height: 15; }
    """
    BINDINGS = [
        ("t", "tab('tags')", "Tags"),
        ("c", "tab('categories')", "Categories"),
        ("n", "sort(0)", "Sort name"),
        ("p", "sort(1)", "Sort posts"),
        ("q", "request_quit", "Quit"),
    ]

    def __init__(self, counts, mapping, path, wp_names):
        super().__init__()
        self.counts, self.mapping, self.path, self.wp_names = (
            counts,
            mapping,
            path,
            wp_names,
        )
        self.sorted_by = {tax: (0, False) for tax in TAXONOMIES}

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tags"):
            for tax in TAXONOMIES:
                with TabPane(tax.capitalize(), id=tax):
                    yield DataTable(
                        id=f"table-{tax}", cursor_type="row", zebra_stripes=True
                    )
        yield Footer()

    def on_mount(self):
        for tax in TAXONOMIES:
            table = self.query_one(f"#table-{tax}", DataTable)
            table.add_column("Hugo", key="hugo")
            table.add_column("Posts", key="count")
            table.add_column("WordPress", key="wp")
            for name in sorted(self.counts[tax], key=str.lower):
                table.add_row(
                    name,
                    self.counts[tax][name],
                    self.mapping[tax].get(name, ""),
                    key=name,
                )
        self.action_tab("tags")

    def action_tab(self, tax):
        self.query_one(TabbedContent).active = tax
        self.query_one(f"#table-{tax}", DataTable).focus()

    def action_sort(self, col):
        tax = self.query_one(TabbedContent).active
        last_col, last_reverse = self.sorted_by[tax]
        # same column again flips; post counts start largest first
        reverse = not last_reverse if col == last_col else col == 1
        self.sorted_by[tax] = (col, reverse)
        sort_key = (
            (lambda row: row[0].lower())
            if col == 0
            else (lambda row: (row[1], row[0].lower()))
        )
        self.query_one(f"#table-{tax}", DataTable).sort(key=sort_key, reverse=reverse)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected):
        if event.column_index < 2:
            self.action_sort(event.column_index)

    def candidates(self, tax):
        # mapped values include new names typed earlier, i.e. WP terms the uploader will create
        names = {*self.wp_names.get(tax, []), *self.mapping[tax].values()}
        return sorted(names, key=str.lower)

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        tax = (event.data_table.id or "").removeprefix("table-")
        name = event.row_key.value or ""

        def apply(value):
            if value is None:
                return
            if value:
                self.mapping[tax][name] = value
            else:
                self.mapping[tax].pop(name, None)
            event.data_table.update_cell(name, "wp", value, update_width=True)

        prompt = Prompt(
            f"Map {tax[:-1]} '{name}' to:",
            self.mapping[tax].get(name, name),
            self.candidates(tax),
        )
        self.push_screen(prompt, apply)

    def action_request_quit(self):
        def done(result):
            if result:
                Path(result).write_text(
                    json.dumps(
                        self.mapping, indent=2, ensure_ascii=False, sort_keys=True
                    )
                    + "\n"
                )
            if result is not None:
                self.exit(result or None)

        self.push_screen(SavePrompt(self.path), done)


def main():
    p = ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument(
        "mapping_file",
        nargs="?",
        default="wordpress-mappings.json",
        help="loaded if it exists",
    )
    p.add_argument("--content", type=Path, default=Path("content/posts"))
    p.add_argument(
        "--url",
        required=True,
        help="WordPress base URL to load terms from (needs WP_USER, WP_APP_PASSWORD)",
    )
    args = p.parse_args()
    wp_names = WP(args.url, os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"]).names

    counts = {tax: Counter() for tax in TAXONOMIES}
    for idx in args.content.glob("**/index.md"):
        fm, _ = read_bundle(idx)
        for tax in TAXONOMIES:
            counts[tax].update(str(t) for t in fm.get(tax) or [])

    mapping = {tax: {} for tax in TAXONOMIES}
    if Path(args.mapping_file).exists():
        mapping.update(json.loads(Path(args.mapping_file).read_text()))

    saved = MappingApp(counts, mapping, args.mapping_file, wp_names).run()
    print(f"saved to {saved}" if saved else "not saved")


if __name__ == "__main__":
    main()
