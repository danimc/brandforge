"""Offline editorial layouts. Presentation SVGs are separate from logo masters."""
from base64 import b64encode
from html import escape
import textwrap

import svg

PAPER = "#F4F0E8"
INK = "#192821"
MUTED = "#46574D"
RULE = "#D5D7CD"
SIZES = (16, 32, 64, 128)


class Sheet:
    def __init__(self, width: int, height: int, title: str):
        self.parts = [f'<svg xmlns="{svg.NS}" xmlns:xlink="http://www.w3.org/1999/xlink" '
                      f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                      f"<title>{escape(title)}</title>"]
        self.rect(0, 0, width, height, PAPER)

    def rect(self, x, y, w, h, color):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')

    def text(self, x, y, value, size=16, color=INK, face="sans-serif", weight=400):
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{face}" '
                          f'font-size="{size}" font-weight="{weight}">{escape(value)}</text>')

    def wrap(self, x, y, value, limit, lines=3, size=16, color=MUTED):
        parts = textwrap.wrap(" ".join(value.split()), width=limit)
        if len(parts) > lines:
            parts[lines - 1] = parts[lines - 1].rstrip(".,;:") + "…"
        for i, line in enumerate(parts[:lines]):
            self.text(x, y + i * (size + 6), line, size, color)

    def art(self, x, y, w, h, data):
        source = b64encode(data).decode("ascii")
        self.parts.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                          f'xlink:href="data:image/svg+xml;base64,{source}"/>')

    def finish(self) -> bytes:
        return ("\n".join(self.parts + ["</svg>"]) + "\n").encode("utf-8")


def header(sheet, label, title, description):
    sheet.text(38, 35, label, 14, MUTED, weight=700)
    sheet.text(38, 83, title, 41, face="serif")
    sheet.wrap(40, 113, description, 85, lines=1, size=15)
    sheet.rect(38, 133, 560, 1, RULE)


def proof(brand: str, master: str, artwork: bytes, grounds: dict) -> bytes:
    sheet = Sheet(640, 903, f"{brand} {master} proof")
    header(sheet, "BRANDFORGE  /  SIZE STUDY", f"{master.capitalize()} proof",
           f"{brand} · sizes show the longest edge of the SVG artboard in pixels")
    for row, (label, ground, data) in enumerate((
        ("01  /  PRIMARY ON LIGHT", grounds["light"], artwork),
        ("02  /  PRIMARY ON DARK", grounds["dark"], artwork),
        ("03  /  BLACK INK", "#FFFFFF", svg.variant(artwork, "#000000")),
        ("04  /  REVERSED INK", "#151A18", svg.variant(artwork, "#FFFFFF")),
    )):
        y = 161 + 180 * row
        sheet.text(38, y, label, 12, MUTED, weight=700)
        for size, x, width in zip(SIZES, (38, 142, 246, 382), (96, 96, 128, 220)):
            sheet.rect(x, y + 10, width, 128, ground)
            sheet.art(x + (width - size) / 2, y + 10 + (128 - size) / 2, size, size, data)
            sheet.text(x, y + 154, f"{size} px", 11, MUTED)
    return sheet.finish()


def comparison(brand: str, cards: list) -> bytes:
    sheet = Sheet(1040, 180 + ((len(cards) + 1) // 2) * 325, f"{brand} creative directions")
    header(sheet, "BRANDFORGE  /  DIRECTION REVIEW", f"{brand} · concept atlas",
           "Original vector sketches · full-size, reversed and compact views")
    for index, (hypothesis, mark, ground) in enumerate(cards):
        x = 38 + (index % 2) * 488
        y = 150 + (index // 2) * 325
        sheet.rect(x, y, 476, 304, "#FFFFFF")
        sheet.text(x + 20, y + 25, f"{index + 1:02}  /  {hypothesis['category'][:38].upper()}", 12, MUTED, weight=700)
        sheet.wrap(x + 20, y + 59, hypothesis["title"], 29, lines=1, size=25, color=INK)
        sheet.rect(x + 20, y + 75, 268, 116, ground)
        sheet.art(x + 104, y + 81, 104, 104, mark)
        sheet.rect(x + 296, y + 75, 160, 116, INK)
        reverse = svg.variant(mark, "#FFFFFF")
        sheet.art(x + 306, y + 99, 68, 68, reverse)
        for size, dx in ((16, 390), (32, 415)):
            sheet.art(x + dx, y + 119 - size / 2, size, size, reverse)
            sheet.text(x + dx, y + 163, str(size), 10, "#E7EDE8")
        sheet.wrap(x + 20, y + 217, hypothesis["metaphor"], 54, lines=2)
        sheet.wrap(x + 20, y + 269, hypothesis["personality"], 59, lines=2, size=13)
    return sheet.finish()


def applications(brand: str, masters: dict, grounds: dict, copy: dict) -> bytes:
    sheet = Sheet(1040, 620, f"{brand} application studies")
    header(sheet, "BRANDFORGE  /  CONTEXT STUDIES", f"{brand} · in use",
           "Illustrative digital and print layouts · reproduction proof remains separate")
    sheet.rect(38, 164, 570, 375, grounds["dark"])
    sheet.text(67, 198, "01  /  " + copy.get("digital_label", "Digital catalog tile")[:36].upper(),
               13, "#FFFFFF", weight=700)
    sheet.art(67, 217, 195, 50, svg.variant(masters["lockup"], "#FFFFFF"))
    sheet.wrap(67, 340, copy["digital_title"], 28, lines=2, size=31, color="#FFFFFF")
    sheet.wrap(68, 444, copy["digital_copy"], 41, lines=3, size=16, color="#FFFFFF")
    sheet.art(442, 330, 135, 135, svg.variant(masters["mark"], "#FFFFFF"))
    sheet.rect(642, 169, 340, 375, "#DADBD1")
    sheet.rect(636, 164, 340, 375, grounds["light"])
    sheet.text(658, 198, "02  /  " + copy.get("print_label", "Print field card")[:36].upper(),
               13, INK, weight=700)
    sheet.art(719, 213, 170, 144, svg.variant(masters["stacked"], "#000000"))
    sheet.rect(659, 381, 294, 1, INK)
    sheet.wrap(659, 413, copy["print_title"], 31, lines=2, size=21, color=INK)
    sheet.wrap(659, 479, copy["print_copy"], 38, lines=3, size=14)
    sheet.text(38, 580, "VECTOR-BASED APPLICATION STUDY   /   NO PHOTOGRAPHIC MOCKUP", 12, MUTED, weight=700)
    return sheet.finish()
