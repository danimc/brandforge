"""Contrast checks for opaque sRGB role pairs."""
from contracts import require

MINIMUM = {"normal-text": 4.5, "large-text": 3, "essential-ui": 3, "logo-target": 3}


def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    red, green, blue = linear
    # Preserve the operation order across Python versions for review fingerprints.
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def audit(tokens):
    reports = []
    for pair in tokens["contrast"]:
        fg, bg = pair["foreground"], pair["background"]
        require(fg in tokens["colors"] and bg in tokens["colors"], f"Unknown contrast role: {fg} / {bg}")
        dark, light = sorted(luminance(tokens["colors"][role]) for role in (fg, bg))
        ratio = (light + 0.05) / (dark + 0.05)
        minimum = MINIMUM[pair["usage"]]
        reports.append({**pair, "ratio": ratio, "minimum": minimum, "pass": ratio >= minimum})
    return reports
