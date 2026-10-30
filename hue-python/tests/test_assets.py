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


class TestAssets:
    def test_the_files_are_where_the_paths_say(self) -> None:
        paths = [p() for p in (css_source_path, css_built_path, js_bundle_path)]
        assert [p.name for p in paths] == [
            "tailwind.input.css",
            "tailwind.css",
            "alpine-bundle.js",
        ]
        assert all(p.exists() for p in paths)
        assert read_css()
        assert "Alpine" in read_js()

    def test_the_chart_library_is_not_in_the_bundle(self) -> None:
        # A page that draws no chart downloads none of it.
        assert _FROM_CHART_JS not in read_js()
        assert _FROM_CHART_JS in read_chart_js()
        # The name the bundle asks for is the one the file has.
        assert chart_bundle_path().name in read_js()
