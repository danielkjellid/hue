from hue_docs import site


def test_url_is_identity_without_base(monkeypatch):
    monkeypatch.setattr(site, "BASE", "")
    assert site.url("/styles/app.css") == "/styles/app.css"
    assert site.url("/") == "/"


def test_url_prefixes_root_relative_paths_with_base(monkeypatch):
    monkeypatch.setattr(site, "BASE", "/hue")
    assert site.url("/") == "/hue/"
    assert site.url("/styles/app.css") == "/hue/styles/app.css"
    assert site.url("/components/button/") == "/hue/components/button/"


def test_url_leaves_external_and_protocol_relative_urls_untouched(monkeypatch):
    monkeypatch.setattr(site, "BASE", "/hue")
    assert site.url("https://example.com/x") == "https://example.com/x"
    assert site.url("//cdn.example.com/x") == "//cdn.example.com/x"
    assert site.url("mailto:a@b.com") == "mailto:a@b.com"
