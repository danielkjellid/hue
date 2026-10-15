from hue.assets import (
    chart_bundle_path,
    css_built_path,
    css_source_path,
    js_bundle_path,
    read_chart_js,
    read_css,
    read_js,
)

# A string from Chart.js's own source, which survives minifying.
_FROM_CHART_JS = "Canvas is already in use"


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

    def test_the_chart_library_is_not_in_the_bundle(self) -> None:
        # A page that draws no chart downloads none of it.
        assert _FROM_CHART_JS not in read_js()
        assert _FROM_CHART_JS in read_chart_js()
        # The name the bundle asks for is the one the file has.
        assert chart_bundle_path().name in read_js()
