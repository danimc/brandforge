"""A portable, offline catalog for curated visual references."""
from typing import Optional
from pathlib import Path
import unicodedata
from urllib.parse import urlsplit

from contracts import digest, json_bytes, require, validate
from image_input import MAX_BYTES, raster_format
import svg


def validate_link(card: dict) -> None:
    if card["storage"] == "link-only":
        url = urlsplit(card["source"])
        require(url.scheme == "https" and url.hostname and not url.username and
                url.password is None and not url.query and not any(ch.isspace() for ch in card["source"]),
                "Link-only references require a public HTTPS URL without credentials or a query")


def entry_files(data: bytes, asset: Optional[Path]) -> tuple[str, dict[str, bytes]]:
    card = validate("library-card", data)
    validate_link(card)
    require((asset is None) == (card["storage"] == "link-only"),
            "Link-only entries omit --asset. Owned or licensed entries require --asset.")
    if asset is None:
        return card["id"], {"card.json": json_bytes(card)}
    require(asset.is_file() and not asset.is_symlink(), "Provide a regular local logo asset")
    with asset.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, "Logo asset exceeds 20 MiB")
    if asset.suffix.lower() == ".svg":
        svg.parse(raw)
        extension = "svg"
    else:
        extension = raster_format(raw)
    card["asset"] = {"name": f"logo.{extension}", "sha256": digest(raw)}
    return card["id"], {"card.json": json_bytes(card), card["asset"]["name"]: raw}


def folded(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(char))


def cards(directory: Path):
    require(directory.is_dir() and not directory.is_symlink(), "Expected a local library directory")
    for entry in sorted(directory.iterdir()):
        path = entry / "card.json"
        if not entry.is_dir() or entry.is_symlink() or not path.exists():
            continue
        require(path.is_file() and not path.is_symlink(), f"Expected regular catalog card: {entry.name}")
        data = validate("library-entry", path.read_bytes())
        require(data["id"] == entry.name, f"Catalog card ID mismatch: {entry.name}")
        validate_link(data)
        require(("asset" in data) == (data["storage"] != "link-only"),
                f"Invalid stored asset policy: {entry.name}")
        yield data


def search(directory: Path, query: str = "", industry: str = "", mark_type: str = "",
           technique: str = "") -> list[dict]:
    matches = []
    for card in cards(directory):
        tags = " ".join(card["techniques"])
        fields = (card["industry"], card["mark_type"], tags)
        filters = (industry, mark_type, technique)
        haystack = folded(" ".join([card["id"], card["title"], *fields, card["observation"]]))
        if (all(folded(value) in folded(field) for value, field in zip(filters, fields))
                and all(term in haystack for term in folded(query).split())):
            matches.append(card)
    return matches


def reference(directory: Path, entry_id: str) -> dict[str, str]:
    card = next((entry for entry in cards(directory) if entry["id"] == entry_id), None)
    require(card is not None, f"Unknown library reference: {entry_id}")
    asset = card.get("asset")
    source = f"Library / {card['id']} / {card['source']}"
    if asset:
        path = directory / entry_id / asset["name"]
        require(path.is_file() and not path.is_symlink(), "Catalog asset is missing")
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES and digest(raw) == asset["sha256"], "Catalog asset hash mismatch")
        source += f" / SHA-256 {asset['sha256']}"
    return {"kind": "research", "source": source,
            "observation": card["observation"], "rights": card["rights"]}
