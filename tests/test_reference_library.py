from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "brandforge.py"
DEMO = ROOT / "examples" / "reference-library"


class LibraryTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.library = self.root / "catalog"
        self.card = self.root / "card.json"
        self.asset = DEMO / "veskil-transect" / "logo.svg"

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, "-B", str(CLI), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout if expected == 0 else result.stderr

    def write_card(self, **overrides):
        card = dict(id="test-reference", title="Trazo orgánico", industry="stationery",
                    mark_type="abstract", techniques=["bezier", "negative-space"],
                    source="Original test asset", rights="Owned test asset",
                    observation="Canal abierto", storage="owned")
        self.card.write_text(json.dumps({**card, **overrides}))

    def test_owned_asset_filters_and_provenance(self):
        self.write_card()
        self.cli("library-add", self.library, self.card, "--asset", self.asset)
        result = json.loads(self.cli("library-search", self.library, "organico canal",
                                     "--industry", "stationery", "--technique", "bezier"))
        self.assertEqual([card["id"] for card in result], ["test-reference"])
        record = json.loads(self.cli("library-reference", self.library, "test-reference"))
        self.assertEqual(record["kind"], "research")
        self.assertIn(result[0]["asset"]["sha256"], record["source"])
        self.cli("library-add", self.library, self.card, "--asset", self.asset, expected=1)
        (self.library / "test-reference" / "logo.svg").write_text("tampered")
        self.assertIn("hash mismatch",
                      self.cli("library-reference", self.library, "test-reference", expected=1))

    def test_external_mark_stays_link_only(self):
        self.write_card(storage="link-only", source="https://example.org/brand")
        self.cli("library-add", self.library, self.card, "--asset", self.asset, expected=1)
        self.assertFalse(self.library.exists())
        self.cli("library-add", self.library, self.card)
        entry = self.library / "test-reference"
        self.assertEqual([path.name for path in entry.iterdir()], ["card.json"])
        self.write_card(id="bad-link", storage="link-only", source="https://example.org/?token=demo")
        self.assertIn("public HTTPS", self.cli("library-add", self.library, self.card, expected=1))

    def test_unsafe_svg_rejected(self):
        self.write_card(storage="licensed", rights="Test fixture only")
        asset = ROOT / "tests" / "fixtures" / "script.svg"
        self.cli("library-add", self.library, self.card, "--asset", asset, expected=1)
        self.assertFalse(self.library.exists())

    def test_demo_cards_resolve_and_raster_import_works(self):
        cards = json.loads(self.cli("library-search", DEMO))
        self.assertEqual(len(cards), 4)
        for card in cards:
            self.cli("library-reference", DEMO, card["id"])
        self.write_card()
        self.cli("library-add", self.library, self.card, "--asset", ROOT / "examples/veskil/preview.png")
        self.assertTrue((self.library / "test-reference" / "logo.png").is_file())
