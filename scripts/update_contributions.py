"""Refresh the public GitHub calendar; Python standard library only."""

import argparse
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen

OUTPUT = Path(__file__).resolve().parents[1] / "assets/contrib-heatmap.svg"
PALETTE = ("#21262d", "#0e4429", "#006d32", "#26a641", "#39d353")


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.counts = {}
        self.tooltip = None
        self.label = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            day = date.fromisoformat(attrs["data-date"])
            level = int(attrs["data-level"])
            if not 0 <= level < len(PALETTE) or day in self.days:
                raise ValueError("Invalid or duplicate calendar day")
            self.days[day] = (attrs["id"], level)
        if tag == "tool-tip":
            self.tooltip = attrs.get("for")
            self.label = []

    def handle_data(self, data):
        if self.tooltip is not None:
            self.label.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tooltip is not None:
            match = re.match(r"\s*(No|[\d,]+) contributions? on\b", "".join(self.label))
            if match:
                self.counts[self.tooltip] = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            self.tooltip = None


def parse_calendar(html):
    # ponytail: public HTML parser; switch to GraphQL if GitHub changes this markup.
    calendar = Calendar()
    calendar.feed(html)
    days = sorted(calendar.days)
    if not 365 <= len(days) <= 371 or (days[-1] - days[0]).days + 1 != len(days):
        raise ValueError("Incomplete contribution calendar; keeping the previous SVG")
    result = []
    for day in days:
        identifier, level = calendar.days[day]
        if identifier not in calendar.counts:
            raise ValueError("Missing contribution count; keeping the previous SVG")
        count = calendar.counts[identifier]
        if (count == 0) != (level == 0):
            raise ValueError("Contribution count and level disagree")
        result.append((day, level, count))
    return result


def render(days):
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    total = sum(count for _, _, count in days)
    span = f"{days[0][0].isoformat()} to {days[-1][0].isoformat()}"
    svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="240" viewBox="0 0 860 240" role="img" aria-labelledby="title desc">
<title id="title">Unknown3663's contribution calendar</title>
<desc id="desc">{total:,} contributions from {span}. Refreshed from GitHub's public calendar.</desc>
<style>
text {{ font-family: ui-monospace, SFMono-Regular, Consolas, monospace; fill: #c9d1d9; }}
.day {{ animation: reveal .45s both; }}
@keyframes reveal {{ from {{ opacity: .2; transform: translateY(-4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@media (prefers-reduced-motion: reduce) {{ .day {{ animation: none; }} }}
</style>
<rect x="1" y="1" width="858" height="238" rx="12" fill="#0d1117" stroke="#30363d"/>
<text x="28" y="33" font-size="14" fill="#79c0ff">unknown@github ~ $ ./contributions.sh</text>''']
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        svg.append(f'<text x="24" y="{77 + row * 17}" font-size="10">{label}</text>')
    last_month = None
    for day, level, count in days:
        week, row = divmod((day - start).days, 7)
        x, y = 62 + week * 14, 65 + row * 17
        if day.month != last_month:
            svg.append(f'<text x="{x}" y="55" font-size="10">{day:%b}</text>')
            last_month = day.month
        svg.append(f'<rect class="day" x="{x}" y="{y}" width="11" height="14" rx="2" fill="{PALETTE[level]}" style="animation-delay:{(week + row) * .018:.3f}s"><title>{count:,} contributions on {day.isoformat()}</title></rect>')
    svg.append(f'<text x="28" y="211" font-size="12">{total:,} contributions · {escape(span)}</text>')
    svg.append('<text x="690" y="211" font-size="10">Less</text>')
    for i, color in enumerate(PALETTE):
        svg.append(f'<rect x="{724 + i * 14}" y="201" width="11" height="11" rx="2" fill="{color}"/>')
    svg.append('<text x="797" y="211" font-size="10">More</text></svg>')
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="Use a saved GitHub calendar for offline checks")
    args = parser.parse_args()
    if args.html:
        html = args.html.read_text(encoding="utf-8")
    else:
        request = Request("https://github.com/users/Unknown3663/contributions", headers={"User-Agent": "Unknown3663-profile-art"})
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8")
    artwork = render(parse_calendar(html))
    OUTPUT.write_text(artwork, encoding="utf-8")
