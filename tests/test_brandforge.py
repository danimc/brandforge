from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "brandforge.py"
FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(CLI.parent))

from contrast import luminance
from svg import parse, variant


class ProfileTests(unittest.TestCase):
    def test_unsafe_svg_is_rejected(self):
        for fixture in FIXTURES.glob("*.svg"):
            with self.subTest(fixture=fixture), self.assertRaises(ValueError):
                parse(fixture.read_bytes())

    def test_invalid_geometry_and_declaration(self):
        shape = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 9 9">{}</svg>'
        for content in ('<path d="M 0 0 L 9 Z" fill="#000000"/>',
                        '<rect x="0" y="0" width="-1" height="9" fill="#FFFFFF"/>',
                        '<g onload="x"/>'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                parse(shape.format(content).encode())
        with self.assertRaises(ValueError):
            parse(b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]>' + shape.format("").encode())

    def test_monochrome_preserves_cutouts(self):
        source = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 9 9"><path fill="#123456" fill-rule="evenodd" d="M 0 0 L 9 0 L 9 9 Z M 2 1 L 7 1 L 7 6 Z"/></svg>'
        _, before = parse(source)
        _, after = parse(variant(source, "#FFFFFF"))
        self.assertEqual(after[0].attrib, {**before[0].attrib, "fill": "#FFFFFF"})

    def test_contrast_endpoints(self):
        self.assertEqual(luminance("#000000"), 0)
        self.assertAlmostEqual(luminance("#FFFFFF"), 1)
        self.assertAlmostEqual(luminance("#777777"), 0.184475, places=6)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.project = self.work / "project"
        shutil.copytree(ROOT / "examples" / "veskil", self.project)
        self.review = self.work / "review"
        self.final = self.work / "final"
        self.spec = self.project / "brand-spec.json"

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, "-B", str(CLI), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout.strip() if expected == 0 else result.stderr

    def read(self, path):
        return json.loads(path.read_text())

    def write(self, path, data):
        path.write_text(json.dumps(data))

    def approve(self, fingerprint):
        spec = self.read(self.spec)
        spec["revision"] += 1
        spec["final_approval"] = {
            "review_sha256": fingerprint,
            "decision": {**spec["concept_approval"], "evidence": "Simulated review approval"},
        }
        approval = self.work / "approval.json"
        self.write(approval, spec)
        return approval

    def test_deterministic_build_and_release(self):
        first = self.cli("build", self.project, self.review)
        self.assertEqual(first, self.cli("build", self.project, self.work / "second"))
        self.assertEqual(first, self.cli("verify", self.review))
        self.assertIn("Explicit final approval", self.cli("release", self.review, self.spec, self.final, expected=1))
        self.assertIn("does not match", self.cli("release", self.review, self.approve("0"*64), self.final, expected=1))
        self.assertEqual(first, self.cli("release", self.review, self.approve(first), self.final))
        self.assertEqual(first, self.cli("verify", self.final, "--released"))
        self.cli("build", self.project, self.review, expected=1)
        self.assertEqual(first, self.cli("verify", self.review))
        (self.final / "tokens.css").write_text("altered")
        self.assertIn("SHA-256 mismatch", self.cli("verify", self.final, "--released", expected=1))

    def test_concept_missing_or_stale(self):
        approved = self.read(self.spec)
        shutil.copyfile(self.project / "revisions/001.json", self.spec)
        self.assertIn("concept selection", self.cli("build", self.project, self.review, expected=1))
        self.write(self.spec, approved)
        concept = self.project / "concepts/field-notch.json"
        concept.write_bytes(concept.read_bytes() + b"\n")
        self.assertIn("Selected concept changed", self.cli("build", self.project, self.review, expected=1))
        self.assertFalse(self.review.exists())

    def test_bad_contrast_blocks_build(self):
        path = self.project / "tokens.json"
        tokens = self.read(path)
        tokens["colors"]["ink"] = "#AAAAAA"
        self.write(path, tokens)
        self.assertIn("Contrast failed", self.cli("build", self.project, self.review, expected=1))
        self.assertFalse(self.review.exists())

    def test_manifest_rejects_extras_and_path_escape(self):
        self.cli("build", self.project, self.review)
        extra = self.review / "extra"
        extra.symlink_to(self.project / "brief.json")
        self.assertIn("Symlink", self.cli("verify", self.review, expected=1))
        extra.unlink()
        extra.write_text("extra")
        self.assertIn("file set mismatch", self.cli("verify", self.review, expected=1))
        extra.unlink()
        manifest = self.review / "manifest.json"
        data = self.read(manifest)
        data["files"]["../outside"] = "0"*64
        self.write(manifest, data)
        self.assertIn("Invalid manifest path", self.cli("verify", self.review, expected=1))

    def test_release_cannot_change_approved_concept_metadata(self):
        fingerprint = self.cli("build", self.project, self.review)
        approval = self.approve(fingerprint)
        data = self.read(approval)
        data["concept_approval"]["evidence"] = "different decision"
        self.write(approval, data)
        self.assertIn("differs", self.cli("release", self.review, approval, self.final, expected=1))
        self.assertFalse(self.final.exists())


if __name__ == "__main__":
    unittest.main()
