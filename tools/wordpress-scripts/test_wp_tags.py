from wp_tags import edit


def test_add_keeps_order_and_skips_duplicates():
    assert edit(["a", "b"], "c") == ["a", "b", "c"]
    assert edit(["a", "B"], "b") == ["a", "B"]


def test_remove_ignores_case_and_missing():
    assert edit(["a", "Foo", "b"], "-foo") == ["a", "b"]
    assert edit(["a"], "-x") == ["a"]
