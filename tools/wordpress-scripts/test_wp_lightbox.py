from wp_lightbox import lightbox, ser, stray_images

LB = '"lightbox":{"enabled":true}'
LINKED = (
    '<p>a -- b &amp; &lt;c&gt;</p>\n\n<!-- wp:gallery {"columns":2,"linkTo":"media"} -->\n<figure class="wp-block-gallery">'
    '<!-- wp:image {"id":1,"sizeSlug":"large","linkDestination":"media"} -->\n'
    '<figure class="wp-block-image size-large"><a href="http://x/a.jpg"><img src="http://x/a-1x1.jpg" alt=""/></a>'
    "</figure>\n<!-- /wp:image --></figure>\n<!-- /wp:gallery -->"
)


def test_gallery_gets_lightbox_and_loses_links():
    out = lightbox(LINKED)
    assert '<!-- wp:gallery {"columns":2,"linkTo":"lightbox"} -->' in out
    assert '<!-- wp:image {"id":1,"sizeSlug":"large","linkDestination":"none",' + LB + "} -->" in out
    assert '<figure class="wp-block-image size-large"><img src="http://x/a-1x1.jpg" alt=""/></figure>' in out
    assert "<p>a -- b &amp; &lt;c&gt;</p>" in out


def test_idempotent_and_untouched_without_change():
    once = lightbox(LINKED)
    assert lightbox(once) == once
    plain = "<p>x&nbsp;y</p>\n\n<!-- wp:paragraph -->\n<p>z</p>\n<!-- /wp:paragraph -->"
    assert lightbox(plain) == plain


def test_single_image_gets_lightbox_custom_link_kept():
    single = '<!-- wp:image {"id":1,"linkDestination":"media"} -->\n<figure><a href="x"><img src="a"/></a></figure>\n<!-- /wp:image -->'
    assert lightbox(single) == (
        '<!-- wp:image {"id":1,"linkDestination":"none",'
        + LB
        + '} -->\n<figure><img src="a"/></figure>\n<!-- /wp:image -->'
    )
    bare = '<!-- wp:image -->\n<figure><img src="a"/></figure>\n<!-- /wp:image -->'
    assert '<!-- wp:image {"linkDestination":"none",' + LB + "} -->" in lightbox(bare)
    custom = '<!-- wp:image {"id":3,"linkDestination":"custom"} -->\n<figure><a href="y"><img src="a"/></a></figure>\n<!-- /wp:image -->'
    assert lightbox(custom) == custom


def test_stray_images():
    assert stray_images('<!-- wp:image -->\n<figure><img src="a"/></figure>\n<!-- /wp:image -->') == 0
    assert stray_images('<p><img src="a"/></p><figure><img src="b"/></figure>') == 2


def test_ser_escapes_like_wordpress():
    assert ser({"a": 'x--<&>"\\'}) == '{"a":"x\\u002d\\u002d\\u003c\\u0026\\u003e\\u0022\\u005c"}'
