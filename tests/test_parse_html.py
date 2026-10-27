from rescue_rag.ingest.parse_html import html_to_text, split_items

TOC = "\n".join(
    f"Item {i}.\nTitle {i}\n{n}"
    for n, i in enumerate(["1", "1A", "1B", "2", "3", "4", "5", "7", "7A", "8"], start=3)
)
BODY = (
    "Item 1. Business\n" + "We make widgets. " * 300 + "\n"
    "Item 1A. Risk Factors\n" + "Risks exist. " * 300 + "\n"
    "Part II, see Item 7 for more.\n"  # mid-line cross-reference must be ignored
    "Item 7. Management's Discussion and Analysis Revenue grew. " + "More. " * 300 + "\n"
    "Item 8. Financial Statements\n" + "Numbers. " * 300
)
DOC = "Table of Contents\n" + TOC + "\n" + "Front matter. " * 300 + "\n" + BODY


def test_toc_is_skipped_and_sections_found():
    sections = {s.item: s for s in split_items(DOC)}
    assert list(sections) == ["1", "1A", "7", "8"]
    assert sections["1"].text.startswith("Item 1. Business")
    assert "We make widgets" in sections["1"].text
    assert "Revenue grew" in sections["7"].text  # title on the same line as body text
    assert "Numbers." in sections["8"].text


def test_no_items():
    assert split_items("just text") == []


def test_html_to_text_removes_hidden_xbrl_and_decodes_cp1252():
    html = (
        '<html><body><div style="display:none">hidden header</div>'
        "<p>Management’s view</p></body></html>"
    ).encode("cp1252")  # the curly apostrophe becomes byte 0x92, invalid as UTF-8
    text = html_to_text(html)
    assert "hidden header" not in text
    assert "Management’s view" in text
