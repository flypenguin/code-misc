# wp_classic_to_blocks.js

Converts every classic-editor post and page to blocks, like the block editor's "Convert to blocks"
button. Runs in the browser's devtools console. What it does in detail: see the comment at the top
of [wp_classic_to_blocks.js](wp_classic_to_blocks.js).

## Before you start

Create a database backup. WordPress keeps a revision of the new content only, so posts that never
had a revision cannot be rolled back without it.

## Run

1. Log in as an administrator and open `wp-admin/post-new.php`. Wait until the editor has loaded,
   do not type anything.
1. Copy the script to the clipboard: `pbcopy < wp_classic_to_blocks.js` (macOS), or open
   the file and copy everything.
1. Open the console: Chrome `Cmd+Opt+J`, Firefox `Cmd+Opt+K`. Paste. Both browsers block the
   first paste: type `allow pasting`, then paste again.
1. Press Enter. This is a dry run. It ends with counts per category, e.g. `converted: 1000`,
   `mixed: 0`, `leftovers: 0`, `missingMedia: 0`, `failed: 0`. Look at the listed posts if
   `mixed`, `leftovers` or `missingMedia` is not 0.
1. Real run: get the code back with the up arrow, change `const APPLY = false;` to `true`, press
   Enter. In Firefox you can also edit in the multi-line editor (`Cmd+B`) and run with
   `Cmd+Enter`. Keep the tab open until `APPLIED` appears.

## Report

| Category       | Meaning                                                                      |
| -------------- | ---------------------------------------------------------------------------- |
| `converted`    | Classic posts converted (dry run: would be converted)                        |
| `mixed`        | Blocks plus classic parts; not touched, convert by hand in the editor        |
| `leftovers`    | Converted, but still contains a Classic or Custom HTML block; check by hand  |
| `missingMedia` | Gallery images whose attachment no longer exists; the image block has no URL |
| `failed`       | Writing the post failed, with the error message                              |

## Afterwards

- Old Hugo shortcodes in the text (`[youtube <id>]`, `[coolplayer]`) end up as Shortcode blocks.
  Replace them by hand: delete the block, paste the YouTube URL, WordPress makes an embed block.
- Converted galleries and images have no lightbox yet. Run `wp_lightbox.py --apply` to set it.
- The next mirror run (`wp2hugo.py`) changes many posts at once, because block HTML differs from
  classic HTML. That is expected.

## Testing locally

[wp-compose](../../compose-stacks/wp-compose/) runs a local copy of the site. `make clean && make up` resets it to the dump.
