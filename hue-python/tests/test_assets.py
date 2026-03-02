from hue.assets import (
    css_built_path,
    css_source_path,
    js_bundle_path,
    read_css,
    read_js,
)


class TestAssetPaths:
    def test_css_source_path_exists(self) -> None:
        path = css_source_path()
        assert path.exists()
        assert path.name == "tailwind.input.css"

    def test_css_built_path_exists(self) -> None:
        path = css_built_path()
        assert path.exists()
        assert path.name == "tailwind.css"

    def test_js_bundle_path_exists(self) -> None:
        path = js_bundle_path()
        assert path.exists()
        assert path.name == "alpine-bundle.js"


class TestAssetContent:
    def test_read_css_returns_content(self) -> None:
        content = read_css()
        assert isinstance(content, str)
        assert len(content) > 0

    def test_read_js_returns_content(self) -> None:
        content = read_js()
        assert isinstance(content, str)
        assert len(content) > 0
        assert "Alpine" in content
