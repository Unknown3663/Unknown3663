"""Convert a supplied portrait into the blog's monochrome, once-only SVG reveal.

Usage: python scripts/make_ascii.py path/to/photo.png
Requires Pillow locally; it is not used by the daily workflow.
"""

from html import escape
from pathlib import Path
import sys
from PIL import Image, ImageEnhance, ImageOps


def portrait(source):
    with Image.open(source) as image:
        image = ImageOps.autocontrast(ImageOps.grayscale(image))
        image = ImageEnhance.Brightness(image).enhance(1.2)
        image = image.resize((72, 44), Image.Resampling.LANCZOS)
    ramp = "@%#*+=-:. "
    svg = ['''<svg xmlns="http://www.w3.org/2000/svg" width="370" height="330" viewBox="0 0 370 330" role="img" aria-labelledby="title desc">
<title id="title">Ezzat's ASCII portrait</title>
<desc id="desc">A monochrome ASCII rendering of Ezzat's GitHub avatar, revealed row by row.</desc>
<style>
.row { animation: print .3s both; }
@keyframes print { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }
@media (prefers-reduced-motion: reduce) { .row { animation: none; } }
</style>
<rect x="1" y="1" width="368" height="328" rx="12" fill="#0d1117" stroke="#30363d"/>
<text x="20" y="29" fill="#79c0ff" font-family="monospace" font-size="12">unknown@arch ~ $ whoami</text>
<g fill="#c9d1d9" font-family="monospace" font-size="7.5" xml:space="preserve">''']
    for row in range(44):
        line = "".join(ramp[min(9, image.getpixel((col, row)) * 10 // 256)] for col in range(72))
        svg.append(f'<text class="row" x="23" y="{52 + row * 5.8:.1f}" textLength="324" lengthAdjust="spacingAndGlyphs" style="animation-delay:{row * .035:.3f}s">{escape(line)}</text>')
    svg.append('</g></svg>')
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "assets/ezzat-ascii.svg"
    output.write_text(portrait(sys.argv[1]), encoding="utf-8")
