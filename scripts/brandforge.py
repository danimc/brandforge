#!/usr/bin/env python3
"""Build, release and verify a Brandforge kit without network dependencies."""
import argparse
from datetime import date
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
from xml.etree.ElementTree import ParseError

from contracts import digest, json_bytes, require, validate
from contrast import audit
import creative
import image_input
import reference_library
import svg

REVIEW_DOCS = ("guidelines.md", "print.md", "visual-review.md")
MANIFEST = "manifest.json"
RECEIPT = "release-spec.json"
CONCEPT_FIELDS = {"concept_id", "concept_sha256", "concept_approval"}
VARIANTS = ("primary", "ink", "reverse")
MASTERS = ("mark", "lockup")


def read(path):
    require(path.is_file() and not path.is_symlink(), f"Expected regular file: {path}")
    return path.read_bytes()


def project_state(project):
    spec = validate("brand-spec", read(project / "brand-spec.json"))
    require(CONCEPT_FIELDS <= spec.keys(), "Explicit concept selection is required")
    date.fromisoformat(spec["concept_approval"]["date"])
    brief = read(project / "brief.json")
    validate("brand-brief", brief)
    require(digest(brief) == spec["brief_sha256"], "Brief changed since concept selection")
    concept = read(project / "concepts" / f"{spec['concept_id']}.json")
    require(validate("concept", concept)["id"] == spec["concept_id"], "Concept ID mismatch")
    require(digest(concept) == spec["concept_sha256"], "Selected concept changed")
    return spec, brief, concept


def css(tokens):
    lines = [":root {"]
    for role, color in sorted(tokens["colors"].items()):
        lines.append(f"  --brand-color-{role}: {color};")
    for role, typography in sorted(tokens["typography"].items()):
        lines.append(f'  --brand-font-{role}: "{typography["family"]}", {typography["fallback"]};')
        lines.append(f'  --brand-weight-{role}: {typography["weight"]};')
    return ("\n".join(lines + ["}", ""])).encode("utf-8")


def kit_files(project):
    spec, brief, concept = project_state(project)
    require("final_approval" not in spec, "Build from a review revision without final approval")
    tokens_data = read(project / "tokens.json")
    tokens = validate("design-tokens", tokens_data)
    reports = audit(tokens)
    failed = [f'{r["foreground"]}/{r["background"]} ({r["usage"]})' for r in reports if not r["pass"]]
    require(not failed, f"Contrast failed: {', '.join(failed)}")
    files = {
        "brief.json": brief,
        "concept.json": concept,
        "brand-spec.json": json_bytes(spec),
        "tokens.json": tokens_data,
        "tokens.css": css(tokens),
        "contrast.json": json_bytes(reports),
    }
    for doc in REVIEW_DOCS:
        files[doc] = read(project / doc)
        require(files[doc].decode("utf-8").strip(), f"Empty review document: {doc}")
    colors = {color.lower() for color in tokens["colors"].values()}
    concept_record = validate("concept", concept)
    state_path = project / creative.STATE
    if any(entry.startswith("comparison-sha256 ") for entry in concept_record["provenance"]):
        require(state_path.exists(), "Approved creative comparison requires creative.json")
    if state_path.exists() or state_path.is_symlink():
        masters, evidence = creative.release_inputs(project, spec["concept_id"], concept_record)
        files.update(evidence)
    else:
        masters = {name: read(project / "source" / f"{name}.svg") for name in MASTERS}
    for name, master in masters.items():
        _, shapes = svg.parse(master)
        require(all(s.get("fill").lower() in colors | {"none"} for s in shapes),
                f"Undeclared brand fill in {name}.svg")
        files[f"logos/{name}-primary.svg"] = master
        files[f"logos/{name}-ink.svg"] = svg.variant(master, "#000000")
        files[f"logos/{name}-reverse.svg"] = svg.variant(master, "#FFFFFF")
    return files


def manifest(files):
    return json_bytes({"schema_version": "1.0", "files": {k: digest(v) for k, v in files.items()}})


def write_new(destination, files):
    destination.mkdir()
    try:
        for name, data in files.items():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    except BaseException:
        shutil.rmtree(destination)
        raise


def inventory(directory):
    require(directory.is_dir() and not directory.is_symlink(), "Expected regular kit directory")
    files = {}
    for item in sorted(directory.rglob("*")):
        require(not item.is_symlink(), f"Symlink in kit: {item}")
        if not item.is_dir():
            files[item.relative_to(directory).as_posix()] = read(item)
    return files


def verified_files(directory, released=False):
    files = inventory(directory)
    require(MANIFEST in files, "Missing manifest.json")
    manifest_data = files.pop(MANIFEST)
    expected = validate("output-manifest", manifest_data)["files"]
    receipt = files.pop(RECEIPT, None)
    require((receipt is not None) == released, "Unexpected or missing release specification")
    mandatory = {"brief.json", "concept.json", "brand-spec.json", "tokens.json", "tokens.css",
                 "contrast.json", *REVIEW_DOCS}
    mandatory.update(f"logos/{mark}-{variant}.svg" for mark in MASTERS for variant in VARIANTS)
    for name in expected:
        path = PurePosixPath(name)
        require(not path.is_absolute() and all(re.fullmatch(r"[a-z0-9][a-z0-9.-]*", p) for p in path.parts)
                and path.as_posix() == name, f"Invalid manifest path: {name}")
    require(mandatory <= expected.keys() and files.keys() == expected.keys(), "Manifest file set mismatch")
    for name, data in files.items():
        require(digest(data) == expected[name], f"SHA-256 mismatch: {name}")
    if released:
        validate_release(receipt, files["brand-spec.json"], manifest_data)
    files[MANIFEST] = manifest_data
    if released:
        files[RECEIPT] = receipt
    return files


def validate_release(receipt, review_spec, manifest_data):
    approved = validate("brand-spec", receipt)
    approval = approved.pop("final_approval", None)
    require(approval is not None, "Explicit final approval is required")
    require(CONCEPT_FIELDS <= approved.keys(), "Release is missing concept approval")
    require(approval["review_sha256"] == digest(manifest_data), "Final approval does not match review manifest")
    date.fromisoformat(approval["decision"]["date"])
    require(approval["decision"]["simulated"] == approved["concept_approval"]["simulated"],
            "Concept and final approval modes must agree")
    reviewed = validate("brand-spec", review_spec)
    require("final_approval" not in reviewed and CONCEPT_FIELDS <= reviewed.keys(), "Invalid review specification")
    require(approved["revision"] == reviewed["revision"] + 1, "Release must be the next spec revision")
    approved["revision"] = reviewed["revision"]
    require(approved == reviewed, "Release specification differs from reviewed decisions")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, paths in {
        "fingerprint": ("file",), "svg": ("file",), "contrast": ("file",),
        "build": ("project", "output"), "verify": ("kit",),
        "release": ("review", "spec", "output"),
    }.items():
        command = commands.add_parser(name)
        for path in paths:
            command.add_argument(path, type=Path)
        if name == "verify":
            command.add_argument("--released", action="store_true")
    for name in ("render", "present", "applications"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        if name != "present":
            command.add_argument("candidate")
        if name == "render":
            command.add_argument("--round", type=int)
        command.add_argument("output", type=Path)
    image_command = commands.add_parser("image-reference")
    image_command.add_argument("file", type=Path)
    for option in ("provider", "observation", "rights"):
        image_command.add_argument(f"--{option}", required=True)
    add = commands.add_parser("library-add")
    add.add_argument("library", type=Path)
    add.add_argument("card", type=Path)
    add.add_argument("--asset", type=Path)
    search = commands.add_parser("library-search")
    search.add_argument("library", type=Path)
    search.add_argument("query", nargs="?", default="")
    for option in ("industry", "mark-type", "technique"):
        search.add_argument(f"--{option}", default="")
    reference = commands.add_parser("library-reference")
    reference.add_argument("library", type=Path)
    reference.add_argument("id")
    args = parser.parse_args()
    try:
        if args.command == "fingerprint":
            print(digest(read(args.file)))
        elif args.command == "svg":
            svg.parse(read(args.file))
            print("SVG profile valid")
        elif args.command == "contrast":
            reports = audit(validate("design-tokens", read(args.file)))
            print(json_bytes(reports).decode("utf-8"), end="")
            return int(any(not report["pass"] for report in reports))
        elif args.command == "image-reference":
            reference = image_input.record(args.file, args.provider, args.observation, args.rights)
            print(json_bytes(reference).decode("utf-8"), end="")
        elif args.command == "library-add":
            entry_id, files = reference_library.entry_files(read(args.card), args.asset)
            args.library.mkdir(exist_ok=True)
            require(not args.library.is_symlink(), "Use a regular library directory")
            write_new(args.library / entry_id, files)
            print(entry_id)
        elif args.command == "library-search":
            matches = reference_library.search(args.library, args.query, args.industry,
                                               args.mark_type, args.technique)
            print(json_bytes(matches).decode("utf-8"), end="")
        elif args.command == "library-reference":
            record = reference_library.reference(args.library, args.id)
            print(json_bytes(record).decode("utf-8"), end="")
        elif args.command == "build":
            files = kit_files(args.project)
            files[MANIFEST] = manifest(files)
            write_new(args.output, files)
            print(digest(files[MANIFEST]))
        elif args.command == "verify":
            files = verified_files(args.kit, args.released)
            print(digest(files[MANIFEST]))
        elif args.command in {"render", "present", "applications"}:
            if args.command == "render":
                packet = creative.render(args.project, args.candidate, args.round)
            elif args.command == "present":
                packet = creative.present(args.project)
            else:
                packet = creative.applications(args.project, args.candidate)
            write_new(args.output, packet)
            print(digest(packet[creative.PACKET]))
        else:
            files = verified_files(args.review)
            receipt = read(args.spec)
            validate_release(receipt, files["brand-spec.json"], files[MANIFEST])
            files[RECEIPT] = receipt
            write_new(args.output, files)
            print(digest(files[MANIFEST]))
    except (OSError, ValueError, ParseError) as error:
        print(f"brandforge: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
