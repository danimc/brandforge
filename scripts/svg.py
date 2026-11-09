"""A deliberately limited static SVG profile for editable logo masters."""
import math
import re
from xml.etree import ElementTree as ET

from contracts import require

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
NUMBER = r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)"
PAINT = re.compile(r"#[0-9a-fA-F]{6}|none")
SHAPES = {
    "path": ("d",),
    "polygon": ("points",),
    "rect": ("x", "y", "width", "height"),
    "circle": ("cx", "cy", "r"),
}
ARITY = {"M": 2, "L": 2, "C": 6, "Q": 4, "Z": 0}


def number(value):
    require(re.fullmatch(NUMBER, value) is not None, f"Invalid SVG number: {value}")
    parsed = float(value)
    require(math.isfinite(parsed) and abs(parsed) <= 1_000_000, "SVG number out of range")
    return parsed


def path_geometry(data):
    # Each subpath starts with M and closes with Z. Every command is explicit.
    tokens = data.split()
    opened = False
    segments = 0
    index = 0
    while index < len(tokens):
        command = tokens[index]
        index += 1
        require(command in ARITY, f"Unsupported or implicit path command: {command}")
        count = ARITY[command]
        require(len(tokens) - index >= count, "Incomplete path command")
        for token in tokens[index:index + count]:
            number(token)
        index += count
        if command == "M":
            require(not opened, "Close the current SVG subpath before starting another")
            opened, segments = True, 0
        else:
            require(opened, "SVG subpath must start with M")
            if command == "Z":
                require(segments > 0, "Empty SVG subpath")
                opened = False
            else:
                segments += 1
    require(data.strip() and not opened, "SVG paths must be nonempty and closed")


def parse(data):
    require(len(data) <= 128_000, "SVG exceeds 128 KB")
    markup = data.decode("utf-8")
    require(chr(0) not in markup and "<!" not in markup and "<?" not in markup, "SVG declarations, comments and DTDs are forbidden")
    root = ET.fromstring(markup)
    require(root.tag == f"{{{NS}}}svg" and set(root.attrib) == {"viewBox"}, "Expected SVG root with viewBox only")
    box = [number(v) for v in root.attrib["viewBox"].split()]
    require(len(box) == 4 and min(box[2:]) > 0, "Invalid SVG viewBox")
    shapes = []
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        require(depth <= 16, "SVG nesting exceeds 16 levels")
        require(not (node.text or "").strip() and not (node.tail or "").strip(), "SVG text is unsupported")
        stack.extend((child, depth + 1) for child in node)
        if node is root:
            continue
        require(node.tag.startswith(f"{{{NS}}}"), "Foreign SVG namespace")
        tag = node.tag.split("}", 1)[1]
        if tag == "g":
            require(not node.attrib, "SVG groups cannot carry attributes")
            continue
        require(tag in SHAPES and not len(node), f"Unsupported SVG element: {tag}")
        geometry = SHAPES[tag]
        require(set(geometry) | {"fill"} <= node.attrib.keys() and
                node.attrib.keys() <= set(geometry) | {"fill", "fill-rule"},
                f"Unsupported or missing SVG attributes on {tag}")
        require(PAINT.fullmatch(node.attrib["fill"]) is not None, "Only solid sRGB fills are supported")
        require(node.attrib.get("fill-rule", "nonzero") in {"nonzero", "evenodd"}, "Invalid fill rule")
        if tag == "path":
            path_geometry(node.attrib["d"])
        elif tag == "polygon":
            coords = [number(v) for v in node.attrib["points"].split()]
            require(len(coords) >= 6 and len(coords) % 2 == 0, "Invalid polygon points")
        else:
            values = [number(node.attrib[key]) for key in geometry]
            require(min(values[2:]) > 0, "SVG shape dimensions must be positive")
        shapes.append(node)
    require(any(node.attrib["fill"] != "none" for node in shapes), "SVG has no painted geometry")
    return root, shapes


def variant(data, fill):
    root, shapes = parse(data)
    for node in shapes:
        if node.attrib["fill"] != "none":
            node.set("fill", fill)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8") + b"\n"
