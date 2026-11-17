/*
 * One-off: convert every classic-editor post and page to blocks, like the block editor's
 * "Convert to blocks" button (block-library freeform: rawHandler({ HTML: serialize(block) })).
 *
 * Run in the browser devtools console on wp-admin/post-new.php, so the block editor and all
 * block types are loaded and wp.apiFetch carries the REST nonce.
 *
 * Only content without any "<!-- wp:" comment is converted. Mixed content (blocks plus classic
 * parts) is only reported. Converted posts that still contain a Classic or Custom HTML block are
 * listed for a manual look.
 *
 * [gallery] shortcodes become image blocks with only an attachment id; the editor fills in the
 * rest while the post is open, so this script does it from the media library instead.
 *
 * Dry run by default; set APPLY = true to write. WP keeps a revision of the new content only, so
 * posts that never had a revision cannot be rolled back: have a DB backup first.
 */
(async () => {
  const APPLY = false;
  const TYPES = ["posts", "pages"];

  const { parse, serialize, rawHandler } = wp.blocks;
  const leftovers = (blocks) =>
    blocks.flatMap((b) => [
      ...(["core/freeform", "core/html"].includes(b.name) ? [b.name] : []),
      ...leftovers(b.innerBlocks),
    ]);
  const images = (blocks) =>
    blocks.flatMap((b) => [...(b.name === "core/image" ? [b] : []), ...images(b.innerBlocks)]);

  // Returns the ids of attachments that no longer exist.
  async function fillImages(blocks) {
    const todo = images(blocks).filter((b) => b.attributes.id && !b.attributes.url);
    if (!todo.length) return [];
    const ids = [...new Set(todo.map((b) => b.attributes.id))];
    const media = await wp.apiFetch({
      path: `/wp/v2/media?context=edit&per_page=100&include=${ids.join(",")}`,
    });
    const byId = new Map(media.map((m) => [m.id, m]));
    for (const b of todo) {
      const m = byId.get(b.attributes.id);
      if (m) Object.assign(b.attributes, { url: m.source_url, alt: m.alt_text, caption: m.caption.raw });
    }
    return ids.filter((id) => !byId.has(id));
  }

  async function* items(type) {
    for (let page = 1, pages = 1; page <= pages; page++) {
      const res = await wp.apiFetch({
        path: `/wp/v2/${type}?context=edit&status=any&per_page=100&page=${page}`,
        parse: false,
      });
      pages = Number(res.headers.get("X-WP-TotalPages")) || 1;
      yield* await res.json();
    }
  }

  const report = { converted: [], mixed: [], leftovers: [], missingMedia: [], failed: [] };
  for (const type of TYPES) {
    for await (const item of items(type)) {
      const raw = item.content.raw;
      const tag = `${type}/${item.id} ${item.slug}`;
      if (!raw.trim()) continue;
      if (raw.includes("<!-- wp:")) {
        if (parse(raw).some((b) => b.name === "core/freeform")) report.mixed.push(tag);
        continue;
      }
      // parse() runs autop on classic content, as the editor does when it loads the post
      const blocks = rawHandler({ HTML: serialize(parse(raw)) });
      const missing = await fillImages(blocks);
      if (missing.length) report.missingMedia.push(`${tag}: ${missing.join(", ")}`);
      const left = leftovers(blocks);
      if (left.length) report.leftovers.push(`${tag}: ${left.join(", ")}`);
      report.converted.push(tag);
      if (!APPLY) continue;
      try {
        await wp.apiFetch({
          path: `/wp/v2/${type}/${item.id}`,
          method: "POST",
          data: { content: serialize(blocks) },
        });
      } catch (e) {
        report.failed.push(`${tag}: ${e.message || e.code}`);
      }
    }
  }

  console.log(APPLY ? "APPLIED" : "DRY RUN (set APPLY = true to write)");
  for (const [k, v] of Object.entries(report)) console.log(`${k}: ${v.length}`, v);
})();
