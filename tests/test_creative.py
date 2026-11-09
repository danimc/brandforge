from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "brandforge.py"
DEMO = ROOT / "examples" / "veskil-creative"
sys.path.insert(0, str(CLI.parent))

import creative
from contracts import digest
import image_input
import studio


class CreativeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / "project"
        shutil.copytree(DEMO, self.project)
        self.output = self.root / "review"

    def cli(self, *args, expected=0):
        run = subprocess.run([sys.executable, "-B", str(CLI), *map(str, args)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, expected, run.stderr)
        return (run.stdout if expected == 0 else run.stderr).strip()

    def change(self, file, edit):
        path = self.project / file
        data = json.loads(path.read_bytes())
        edit(data)
        path.write_text(json.dumps(data))

    def test_creative_end_to_end_matches_fixture(self):
        expected = (DEMO / "expected-manifest.json").read_bytes()
        fingerprint = self.cli("build", self.project, self.output)
        self.assertEqual(fingerprint, digest(expected))
        self.assertEqual((self.output / "manifest.json").read_bytes(), expected)
        self.assertEqual(len(list((self.output / "logos").glob("*.svg"))), 9)
        final = self.root / "final"
        self.assertEqual(self.cli("release", self.output, self.project / "revisions/003.json", final),
                         fingerprint)
        self.assertEqual(self.cli("verify", final, "--released"), fingerprint)

    def test_rejects_stale_raster_inputs_and_inspection(self):
        master = self.project / "creative/transect/r2/mark.svg"
        data = master.read_bytes()
        master.write_bytes(data.replace(b"M 5 40", b"M 7 40", 1))
        self.assertIn("Stale proof packet", self.cli("build", self.project, self.output, expected=1))
        master.write_bytes(data)
        self.change("creative/transect/r2/inspection.json", lambda r: r.update(packet_sha256="0"*64))
        self.assertIn("Inspection does not match", self.cli("build", self.project, self.output, expected=1))
        self.assertFalse(self.output.exists())

    def test_tampered_board_blocks_build(self):
        (self.project / "creative/comparison/comparison.png").write_bytes(b"not the approved image")
        self.assertIn("Modified comparison artifact", self.cli("build", self.project, self.output, expected=1))

    def test_latest_round_must_have_review_and_preceding_critique(self):
        def decision(value):
            return lambda r: r.update(decision=value)
        self.change("creative/transect/r2/inspection.json", decision("refine"))
        self.assertIn("must mark this round ready", self.cli("build", self.project, self.output, expected=1))
        self.change("creative/transect/r2/inspection.json", decision("ready"))
        self.change("creative/transect/r1/inspection.json", decision("ready"))
        self.assertIn("prior critique", self.cli("build", self.project, self.output, expected=1))

    def test_shortlist_contract_and_mode(self):
        self.change("creative.json", lambda state: state["candidates"].pop("index-type"))
        with self.assertRaisesRegex(ValueError, "Shortlist must match"):
            creative.state_data(self.project)
        shutil.copyfile(DEMO / "creative.json", self.project / "creative.json")
        self.change("creative.json", lambda state: state.update(mode="hybrid"))
        with self.assertRaisesRegex(ValueError, "generated-image provenance"):
            creative.state_data(self.project)

    def test_approved_creative_state_cannot_fall_back_to_legacy(self):
        (self.project / "creative.json").unlink()
        self.assertIn("requires creative.json", self.cli("build", self.project, self.output, expected=1))

    def test_provider_neutral_raster_provenance(self):
        image = DEMO / "creative/comparison/comparison.png"
        record = image_input.record(image, "Example provider", "Study relative scale", "Demo rights")
        self.assertIn(digest(image.read_bytes()), record["source"])
        self.assertNotIn(str(image.parent), record["source"])
        with self.assertRaisesRegex(ValueError, "Expected PNG or JPEG"):
            image_input.record(DEMO / "creative.json", "Example", "Study", "Demo rights")

    def test_board_escapes_untrusted_copy(self):
        data = (DEMO / "creative/transect/r2/mark.svg").read_bytes()
        proof = studio.proof("<unsafe & name>", "mark", data,
                             {"light": "#FFFFFF", "dark": "#000000"})
        self.assertIn(b"&lt;unsafe &amp; name&gt;", proof)
        self.assertNotIn(b"<unsafe", proof)
        for size in studio.SIZES:
            self.assertIn(f"{size} px".encode(), proof)

    @unittest.skipUnless(shutil.which("rsvg-convert"), "optional librsvg renderer unavailable")
    def test_real_renderer_rebuilds_only_one_candidate(self):
        before = (self.project / "creative/folded-v/r1/proof/packet.json").read_bytes()
        result = self.cli("render", self.project, "transect", self.output)
        packet = json.loads((self.output / "packet.json").read_bytes())
        self.assertEqual(result, digest((self.output / "packet.json").read_bytes()))
        self.assertIn("rsvg-convert version", packet["renderer"])
        self.assertEqual((self.output / "mark.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual((self.project / "creative/folded-v/r1/proof/packet.json").read_bytes(), before)
        atlas = self.root / "atlas"
        self.cli("present", self.project, atlas)
        self.assertTrue((atlas / "comparison.png").is_file())
        application = self.root / "application"
        self.cli("applications", self.project, "transect", application)
        self.assertTrue((application / "applications.png").is_file())


if __name__ == "__main__":
    unittest.main()
