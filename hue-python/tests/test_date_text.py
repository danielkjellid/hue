"""
The server and date-text.js write a date field's text twice, once on the
page and once in the browser, so the two are compared through node. The
browser reads it back too, and the server refuses a format whose text it
would not, so the two are held to the same answer.
"""

import json
import shutil
import subprocess
from datetime import date, datetime, time
from pathlib import Path

import pytest

import hue
from hue.formats import DAY_DIRECTIVES, TIME_DIRECTIVES, Formats
from hue.ui.molecules import date_input

_JS = Path(hue.__file__).parent / "static" / "js"
_NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(_NODE is None, reason="node is not on PATH")

_SCRIPT = """
import { monthFirst, parseDay, parseMoment, parseTime, strftime } from %s;
import { PRESETS } from %s;
let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
	const { names, cases } = JSON.parse(input);
	const written = cases.map(([pattern, value]) => strftime(pattern, value, names));
	// Read as date-input.js reads its field, null where it reads nothing.
	const read = cases.map(([pattern], i) => {
		const today = "2026-10-21";
		const options = { ...names, monthFirst: monthFirst(pattern), today };
		const text = written[i];
		if (!/%%-?[demYBbAa]/.test(pattern)) return parseTime(text);
		if (!/%%-?[HIMp]/.test(pattern)) return parseDay(text, options);
		const moment = parseMoment(text, options);
		return moment && `${moment.day}T${moment.time}`;
	});
	const presets = Object.keys(PRESETS);
	process.stdout.write(JSON.stringify({ written, read, presets }));
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


_NAMES = {
    "monthNames": list(Formats().month_names),
    "monthAbbreviations": list(Formats().month_abbreviations),
    "dayNames": list(Formats().day_names),
    "dayAbbreviations": list(Formats().day_abbreviations),
}


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
    written = _browser(_NAMES, cases)["written"]
    pairs = zip(cases, written, expected, strict=True)
    assert [(case, w, e) for case, w, e in pairs if w != e][:5] == []


def test_the_presets_are_the_ones_the_server_draws():
    assert _browser({}, [])["presets"] == list(date_input._PRESETS)


# A day past the twelfth, so a day and month read the wrong way round do
# not come back as the same date, and a time past noon.
_VALUES = {"date": "2026-10-25", "datetime": "2026-10-25T14:30", "time": "14:30"}
_READABLE = {
    "date": [
        "%Y-%m-%d", "%Y/%m/%d", "%Y. %m. %d.", "%d.%m.%Y", "%d.%m.%Y.",
        "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y", "%-d.%-m.%Y",
        "%d %B %Y", "%-d. %B %Y", "%e %b %Y", "%B %-d, %Y", "%A %d %B %Y",
        "%a, %b %d, %Y", "%A, %d.%m.%Y",
    ],
    "datetime": [
        "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d.%m.%Y %H:%M", "%d.%m.%Y. %H.%M",
        "%m/%d/%Y %I:%M %p", "%Y-%m-%d %-I.%M%p", "%d %B %Y, %H:%M",
    ],
    "time": ["%H:%M", "%H.%M", "%H%M", "%I:%M %p", "%-I:%M%p"],
}  # fmt: skip
_REFUSED = {
    "date": [
        "%d/%m/%y", "%B %Y", "%d %B %Y (%a)", "%d %B %Y, %A", "%Y %d %m",
        "%d.%m.%Y %%", "%d, %m, %Y",
    ],
    "datetime": [
        "%d.%m.%Y kl. %H:%M", "%H:%M %d.%m.%Y", "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %I:%M", "%d.%m.%Y %H",
    ],
    "time": ["%I:%M", "%M:%H", "%H:%M:%S", "%-I%p", "%H"],
}  # fmt: skip


def test_a_format_is_refused_exactly_when_its_text_does_not_read_back():
    cases = [
        (kind, pattern)
        for table in (_READABLE, _REFUSED)
        for kind, patterns in table.items()
        for pattern in patterns
    ]
    read = _browser(_NAMES, [(p, _VALUES[k]) for k, p in cases])["read"]
    answers = {
        (kind, pattern): (
            bool(date_input._READABLE[kind][0].fullmatch(pattern)),
            got == _VALUES[kind],
        )
        for (kind, pattern), got in zip(cases, read, strict=True)
    }
    readable = {(k, p) for k, ps in _READABLE.items() for p in ps}
    wrong = {case: a for case, a in answers.items() if a != (case in readable,) * 2}
    assert wrong == {}


def test_a_name_with_marks_and_joiners_reads_back():
    # Hindi spells its vowels as marks on a letter, not as letters, and
    # Kannada and Malayalam join letters with an invisible joiner, as in
    # August here.
    names = {
        **_NAMES,
        "monthNames": (
            "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त\u200d सितंबर अक्टूबर नवंबर दिसंबर"
        ).split(),
        "dayAbbreviations": "सोम मंगल बुध गुरु शुक्र शनि रवि".split(),
    }
    days = [f"2026-{month:02}-15" for month in range(1, 13)]
    assert _browser(names, [("%a %d %B %Y", day) for day in days])["read"] == days


def test_a_byte_order_mark_after_a_name_is_read_as_a_space():
    # JavaScript counts U+FEFF as whitespace, and a name must not swallow it.
    imported = json.dumps((_JS / "date-text.js").as_uri())
    typed = json.dumps("20 oct\N{ZERO WIDTH NO-BREAK SPACE} 2026")
    options = json.dumps({**_NAMES, "monthFirst": False, "today": "2026-10-21"})
    script = f"import {{ parseDay }} from {imported};"
    script += f"console.log(JSON.stringify(parseDay({typed}, {options})));"
    done = subprocess.run(
        [str(_NODE), "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(done.stdout) == "2026-10-20"
