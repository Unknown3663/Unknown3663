"""Run with: python3 -m unittest discover -s scripts -p 'test_*.py'."""

from datetime import date, timedelta
import unittest
import xml.etree.ElementTree as ET
from update_contributions import parse_calendar, render


class ProfileArtTest(unittest.TestCase):
    def test_calendar_counts_layout_and_invalid_responses(self):
        start = date(2025, 10, 5)
        html = []
        for i in range(367):
            count, level = (1234, 4) if i == 5 else (0, 0)
            label = "1,234 contributions" if count else "No contributions"
            html.append(f'<td id="day-{i}" data-date="{start + timedelta(days=i)}" data-level="{level}"></td><tool-tip for="day-{i}">{label} on a date.</tool-tip>')
        html = "".join(html)
        days = parse_calendar(html)
        self.assertEqual(sum(count for _, _, count in days), 1234)
        svg = ET.fromstring(render(days))
        cells = svg.findall('.//{http://www.w3.org/2000/svg}rect[@class="day"]')
        self.assertEqual(len(cells), 367)
        self.assertEqual(cells[0].attrib["y"], "65")  # Sunday starts the top row.
        self.assertTrue(all(float(cell.attrib["x"]) + 11 < 860 for cell in cells))
        self.assertIn("1,234 contributions", render(days))
        for invalid in ("", html.replace("No contributions", "unknown"), html.replace('data-level="4"', 'data-level="9"'), html + html):
            with self.assertRaises(ValueError):
                parse_calendar(invalid)


if __name__ == "__main__":
    unittest.main()
