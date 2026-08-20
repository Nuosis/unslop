import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from dossier.render import render
from dossier.ids import scrub, find


def _html(doc): return render(doc)[0]


def test_identifiers_never_reach_the_page():
    doc = {"title": "t", "sections": [
        {"type": "list", "items": [
            "task:system_ops:4264401785c5cab3367d64fa is consolidated",
            "branch f5bcfc0 merged into 94db0e7",
            "session 5b0381e4-c4a5-4a92-85be-2e6ff12053fe closed"]}]}
    html, meta = render(doc)
    assert meta["identifiers"], "identifiers should be captured for the agent"
    for ident in meta["identifiers"]:
        assert ident not in html, f"{ident} leaked onto the page"


def test_facts_a_reader_acts_on_survive():
    keep = ["$500", "2026-08-19", "37 passed", "+1 778 678 3674", "1.2.31", "9:30"]
    html = _html({"title": "t", "sections": [{"type": "list", "items": keep}]})
    for k in keep:
        assert k in html, f"{k} was wrongly scrubbed"


def test_agent_cannot_inject_markup_or_script():
    doc = {"title": "<script>alert(1)</script>", "sections": [
        {"type": "record", "fields": {"<img src=x onerror=alert(1)>": "<b>bold</b>"}}]}
    html = _html(doc)
    # The safety property is that agent text cannot become markup, not that
    # dangerous-looking substrings are absent -- escaped text is inert.
    assert "<script" not in html and "<img" not in html
    assert "&lt;script&gt;" in html and "&lt;img" in html
    assert "<b>bold</b>" not in html and "&lt;b&gt;" in html


def test_unknown_shape_renders_and_is_logged_not_dropped():
    html, meta = render({"title": "t", "sections": [
        {"type": "sankey", "heading": "Flow", "a": "1"}]})
    assert meta["unknown_shapes"] == ["sankey"]
    assert "Flow" in html and meta["sections"] == 1


def test_all_six_elements_render():
    doc = {"title": "t", "sections": [
        {"type": "list", "items": ["a"]},
        {"type": "record", "fields": {"k": "v"}},
        {"type": "timeline", "events": [{"when": "Tue", "what": "x"}]},
        {"type": "status_table", "rows": [{"label": "l", "status": "blocked", "detail": "d"}]},
        {"type": "decision", "question": "q", "options": [{"name": "A", "recommended": True}]},
        {"type": "metric", "metrics": [{"value": "5", "label": "failures"}]}]}
    html, meta = render(doc)
    assert meta["sections"] == 6 and meta["unknown_shapes"] == []
    assert "pill bad" in html and "opt rec" in html


def test_page_is_self_contained_and_locked_down():
    html = _html({"title": "t", "sections": []})
    assert "default-src 'none'" in html
    assert "http://" not in html and "https://" not in html, "no external requests"
    assert "<script" not in html


def test_theme_covers_both_schemes():
    html = _html({"title": "t", "sections": []})
    assert "prefers-color-scheme:dark" in html and "[data-theme=dark]" in html


def test_scrub_is_idempotent():
    s = "task:abc:1234567 and f5bcfc0"
    assert scrub(scrub(s)) == scrub(s)


def test_empty_document_is_valid():
    html, meta = render({})
    assert "<!doctype html>" in html and meta["sections"] == 0
