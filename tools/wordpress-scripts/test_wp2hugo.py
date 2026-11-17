from wp2hugo import Bundle, Media, convert, generated, post_dir, stale

HOST = "wp.example"
UP = "http://wp.example/wp-content/uploads/2020/05"
MEDIA = Media(
    [
        {
            "id": 7,
            "source_url": f"{UP}/a.jpg",
            "media_details": {"sizes": {"medium": {"source_url": f"{UP}/a-300x200.jpg"}}},
        },
        {"id": 8, "source_url": f"{UP}/b.jpg", "media_details": []},
    ]
)


def md(html):
    bundle, warnings = Bundle(MEDIA), []
    return convert(html, HOST, bundle, warnings.append), bundle, warnings


def test_ref_links_dedupe_and_internal_rewrite():
    out, _, _ = md(
        '<p><a href="http://wp.example/2026/11/09/slug/">in</a> <a href="https://x.org/">out</a> '
        '<a href="https://x.org/">again</a></p>'
    )
    assert "[in][1] [out][2] [again][2]" in out
    assert out.endswith("[1]: /2026/11/09/slug/\n[2]: https://x.org/\n")


def test_link_to_media_variant_uses_bundle_filename():
    out, bundle, _ = md(f'<p><a href="{UP}/a-300x200.jpg">pic</a></p>')
    assert "[1]: a.jpg" in out
    assert bundle.files == {"a.jpg": f"{UP}/a.jpg"}


def test_figure_class_width_caption_link():
    html = (
        f'<figure class="wp-block-image alignwide is-style-rounded size-large"><a href="http://wp.example/x/">'
        f'<img src="{UP}/a.jpg" alt="A &quot;q&quot;" width="640" class="wp-image-7 foo"></a>'
        "<figcaption>Cap <b>tion</b></figcaption></figure>"
    )
    out, _, _ = md(html)
    assert out == (
        '{{< figure src="a.jpg" alt="A \\"q\\"" caption="Cap tion" class="alignwide is-style-rounded" '
        'width="640" link="/x/" >}}\n'
    )


def test_image_resolved_via_size_variant_url_and_id():
    out, bundle, warnings = md(f'<img src="{UP}/a-300x200.jpg"><img src="{UP}/gone-1x1.jpg" class="wp-image-8">')
    assert out.count('src="a.jpg"') == 1 and 'src="b.jpg"' in out
    assert bundle.names == {7: "a.jpg", 8: "b.jpg"} and not warnings


def test_unresolved_image_warns():
    out, _, warnings = md('<img src="http://elsewhere/z.png">')
    assert 'src="http://elsewhere/z.png"' in out and len(warnings) == 1


def test_basename_clash_gets_id_prefix():
    media = Media([{"id": 1, "source_url": f"{UP}/x.jpg"}, {"id": 2, "source_url": "http://wp.example/o/x.jpg"}])
    b = Bundle(media)
    assert (b.add(1), b.add(2)) == ("x.jpg", "2-x.jpg")


def test_gallery_block_and_classic():
    block = (
        '<figure class="wp-block-gallery has-nested-images columns-2"><figure class="wp-block-image">'
        f'<img src="{UP}/a.jpg"><figcaption>one</figcaption></figure><figure class="wp-block-image">'
        f'<img src="{UP}/b.jpg"></figure></figure>'
    )
    out, _, _ = md(block)
    assert out == (
        '{{< gallery columns="2" >}}\n{{< figure src="a.jpg" caption="one" >}}\n'
        '{{< figure src="b.jpg" >}}\n{{< /gallery >}}\n'
    )
    classic = (
        "<div class='gallery galleryid-1 gallery-columns-4'><dl class='gallery-item'><dt class='gallery-icon'>"
        f"<a href='{UP}/a.jpg'><img src='{UP}/a-300x200.jpg'></a></dt>"
        "<dd class='wp-caption-text gallery-caption'>cap</dd></dl></div>"
    )
    out, _, _ = md(classic)
    assert (
        out == '{{< gallery columns="4" >}}\n{{< figure src="a.jpg" caption="cap" link="a.jpg" >}}\n{{< /gallery >}}\n'
    )


def test_youtube_iframe_and_text():
    out, _, _ = md(
        '<iframe src="https://www.youtube.com/embed/abc_1-2?feature=oembed"></iframe><p>x [youtube Q9w-e_1] y</p>'
    )
    assert "{{< youtube abc_1-2 >}}" in out and "{{< youtube Q9w-e_1 >}}" in out
    assert "[youtube" not in out


def test_generated_listing_pages_are_skipped():
    def item(raw):
        return {"content": {"raw": raw}}

    assert generated(item('<!-- wp:tag-cloud {"showTagCounts":true} /-->'))
    assert generated(item("<!-- wp:archives /-->\n\n<!-- wp:latest-posts /-->"))
    assert not generated(item("<!-- wp:tag-cloud /-->\n<!-- wp:paragraph --><p>x</p><!-- /wp:paragraph -->"))
    assert not generated(item("<p>classic</p>"))
    assert not generated({"content": {"rendered": "<p>anonymous</p>"}})


def test_typographic_quotes_and_ellipsis_become_ascii():
    out, _, _ = md(
        f"<p>&#8222;a&#8220; &#8216;b&#8217; &raquo;c&laquo; d&#8230;&nbsp;e &#8211;</p><img src='{UP}/a.jpg' alt='&#8220;q&#8221;'>"
    )
    assert out.startswith('"a" \'b\' "c" d... e ' + chr(0x2013))
    assert 'alt="\\"q\\""' in out


def test_stale_by_size(tmp_path):
    f = tmp_path / "a.jpg"
    assert stale(f, 3)
    f.write_bytes(b"abc")
    assert not stale(f, 3) and not stale(f, None)
    assert stale(f, 4)


def test_post_dir():
    post = {"id": 5, "date": "2016-06-24T10:30:00", "slug": "still-hier"}
    assert str(post_dir(post)) == "content/posts/2016/2016-06-24-1030-still-hier"
    draft = {"id": 5, "date": "2016-06-24T10:30:00", "slug": "", "generated_slug": "gen"}
    assert post_dir(draft).name == "2016-06-24-1030-gen"
    assert post_dir({**draft, "generated_slug": ""}).name == "2016-06-24-1030-5"
