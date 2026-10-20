"""
The server and date-text.js write a date field's text twice, once on the
page and once in the browser, so the two are compared through node.
"""

import json
import shutil
import subprocess
from datetime import date, datetime, time
from pathlib import Path

import pytest

import hue
from hue.formats import DAY_DIRECTIVES, TIME_DIRECTIVES, Formats
from hue.ui.molecules.date_input import _PRESETS

_JS = Path(hue.__file__).parent / "static" / "js"
_NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(_NODE is None, reason="node is not on PATH")

_SCRIPT = """
import { strftime } from %s;
import { PRESETS } from %s;
let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
	const { names, cases } = JSON.parse(input);
	const written = cases.map(([pattern, value]) => strftime(pattern, value, names));
	process.stdout.write(JSON.stringify({ written, presets: Object.keys(PRESETS) }));
});
"""


def _browser(names: dict[str, list[str]], cases: list[tuple[str, str]]) -> dict:
    script = _SCRIPT % (
        json.dumps((_JS / "date-text.js").as_uri()),
        json.dumps((_JS / "date-input.js").as_uri()),
    )
    done = subprocess.run(
        [str(_NODE), "--input-type=module", "-e", script],
        input=json.dumps({"names": names, "cases": cases}),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout)


def test_every_directive_is_written_as_the_browser_writes_it():
    formats = Formats()
    days = " ".join(f"%{d}" for d in DAY_DIRECTIVES) + " %%"
    times = " ".join(f"%{d}" for d in TIME_DIRECTIVES) + " %%"
    expected: list[str] = []
    cases: list[tuple[str, str]] = []
    # Every year a field accepts, each on a different month, day and time.
    for year in range(1, 10000):
        day = date(year, year % 12 + 1, year % 28 + 1)
        clock = time(year * 37 % 1440 // 60, year * 37 % 60)
        moment = datetime.combine(day, clock)
        for pattern, value, iso in (
            (days, day, day.isoformat()),
            (times, clock, clock.isoformat(timespec="minutes")),
            (f"{days} {times}", moment, moment.isoformat(timespec="minutes")),
        ):
            cases.append((pattern, iso))
            expected.append(formats.write(pattern, value))
    names = {
        "monthNames": list(formats.month_names),
        "monthAbbreviations": list(formats.month_abbreviations),
        "dayNames": list(formats.day_names),
        "dayAbbreviations": list(formats.day_abbreviations),
    }
    written = _browser(names, cases)["written"]
    pairs = zip(cases, written, expected, strict=True)
    assert [(case, w, e) for case, w, e in pairs if w != e][:5] == []


def test_the_presets_are_the_ones_the_server_draws():
    assert _browser({}, [])["presets"] == list(_PRESETS)
