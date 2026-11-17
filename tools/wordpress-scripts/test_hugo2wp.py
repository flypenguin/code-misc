from hugo2wp import convert, map_terms


def test_map_terms():
    mapping = {"leben": "Leben", "das rockt": "Musik", "kram": "kram"}
    assert map_terms(mapping, ["leben", "das rockt", "musik", "kram", "neu", 2011]) == [
        "Leben",
        "Musik",
        "kram",
        "neu",
        "2011",
    ]
    assert map_terms(mapping, None) == []


def test_convert():
    body = (
        '[x]({{< relref "2010-12-28-blake" >}}) [y]({{< ref other.md >}})\n\n'
        '{{< figure src="images/a.jpg" alt="A" width="50%" >}}\n'
        "![b](b.png)\n\n"
        '{{< lightgallery thumbtype="fill" >}}\n'
        "{{< youtube abc_1-2 >}}\n"
    )
    media = {"images/a.jpg": (7, "https://wp/a.jpg"), "b.png": (3, "https://wp/b.png")}
    html = convert(body, media, {"2010-12-28-blake": "/2010/12/28/blake/", "other": "/o/"})
    assert 'href="/2010/12/28/blake/"' in html
    assert 'href="/o/"' in html
    assert '<img src="https://wp/a.jpg" alt="A" style="width:50%">' in html
    assert 'src="https://wp/b.png"' in html
    assert '[gallery ids="3,7"]' in html
    assert "<p>https://www.youtube.com/watch?v=abc_1-2</p>" in html
    assert "{{<" not in html


def test_escaped_angle_bracket():
    assert convert("a \\<klatsch> b", {}, {}) == "<p>a &lt;klatsch&gt; b</p>"
