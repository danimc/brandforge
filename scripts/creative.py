"""Creative project state and render evidence. Design judgments belong to the host."""
from pathlib import Path
from xml.etree.ElementTree import canonicalize

from contracts import digest, json_bytes, require, validate
from contrast import luminance
from renderer import Rsvg
import studio
import svg

MASTERS = ("mark", "lockup", "stacked")
PACKET = "packet.json"
STATE = "creative.json"


def project_file(path: Path) -> bytes:
    require(path.is_file() and not path.is_symlink(), f"Expected regular file: {path}")
    return path.read_bytes()


def hashes(files: dict[str, bytes]) -> dict[str, str]:
    return {name: digest(data) for name, data in files.items()}


def state_data(project: Path):
    brief_data = project_file(project / "brief.json")
    brief = validate("brand-brief", brief_data)
    raw = project_file(project / STATE)
    state = validate("creative-state", raw)
    require(state["brief_sha256"] == digest(brief_data), "Creative brief fingerprint is stale")
    hypotheses = {item["id"]: item for item in state["hypotheses"]}
    require(len(hypotheses) == len(state["hypotheses"]), "Duplicate hypothesis ID")
    shortlisted = {key for key, item in hypotheses.items() if item["decision"] == "shortlisted"}
    require(3 <= len(shortlisted) <= 6 and shortlisted == state["candidates"].keys(),
            "Shortlist must match candidates and contain 3 to 6 IDs")
    require(state["mode"] == "vector-first" or
            any(ref["kind"] == "generated-image" for ref in state["references"]),
            "Image-assisted and hybrid modes require generated-image provenance. Record vector-first for fallback.")
    require((luminance(state["grounds"]["light"]) + .05) /
            (luminance(studio.INK) + .05) >= 4.5 and
            1.05 / (luminance(state["grounds"]["dark"]) + .05) >= 4.5,
            "Use a light and dark ground with enough contrast for presentation text")
    return raw, state, brief


def round_inputs(project, candidate, revision, state, brief):
    directory = project / "creative" / candidate / f"r{revision}"
    note = project_file(directory / "iteration.json")
    validate("creative-iteration", note)
    masters = {}
    technical = {}
    for name in MASTERS:
        path = directory / f"{name}.svg"
        if name == "mark" or path.exists() or path.is_symlink():
            data = project_file(path)
            root, shapes = svg.parse(data)
            masters[name] = data
            technical[name] = {"sha256": digest(data), "view_box": root.get("viewBox"),
                               "shape_count": len(shapes), "static_svg_profile": "pass"}
    inputs = hashes({f"{key}.svg": data for key, data in masters.items()})
    inputs.update(hashes({"iteration.json": note, "grounds.json": json_bytes(state["grounds"]),
                          "brief.json": json_bytes(brief)}))
    return directory, masters, technical, inputs


def packet_files(kind, inputs, sheets, attachments=None, renderer=None):
    renderer = renderer or Rsvg.discover()
    result = dict(attachments or {})
    for name, data in sheets.items():
        result[f"{name}.svg"] = data
        result[f"{name}.png"] = renderer.png(data)
    result[PACKET] = json_bytes({"schema_version": "0.2", "kind": kind,
                                 "renderer": renderer.version, "inputs": inputs,
                                 "files": hashes(result)})
    return result


def verify_packet(directory, kind, names, inputs=None):
    raw = project_file(directory / PACKET)
    packet = validate("creative-packet", raw)
    require(packet["kind"] == kind, f"Expected {kind} packet at {directory}")
    require(packet["files"].keys() == set(names), f"Unexpected {kind} artifact set")
    require(inputs is None or packet["inputs"] == inputs, f"Stale {kind} packet at {directory}")
    files = {name: project_file(directory / name) for name in names}
    require(hashes(files) == packet["files"], f"Modified {kind} artifact at {directory}")
    require(all(data.startswith(b"\x89PNG\r\n\x1a\n") for name, data in files.items()
                if name.endswith(".png")), f"Invalid PNG in {kind} packet")
    files[PACKET] = raw
    return files, packet


def sheet_names(names):
    return {f"{name}.{ext}" for name in names for ext in ("svg", "png")}


def proof_packet(project, candidate, revision, state, brief):
    directory, masters, _, inputs = round_inputs(project, candidate, revision, state, brief)
    names = sheet_names(masters) | {"technical.json"}
    files, _ = verify_packet(directory / "proof", "proof", names, inputs)
    return directory, masters, files


def render(project, candidate, revision=None, renderer=None):
    _, state, brief = state_data(project)
    require(candidate in state["candidates"], f"Unknown candidate: {candidate}")
    active = state["candidates"][candidate]
    revision = active if revision is None else revision
    require(1 <= revision <= active, "Requested round is outside recorded history")
    _, masters, technical, inputs = round_inputs(project, candidate, revision, state, brief)
    sheets = {name: studio.proof(brief["name"], name, data, state["grounds"]) for name, data in masters.items()}
    return packet_files("proof", inputs, sheets, {"technical.json": json_bytes(technical)}, renderer)


def present(project, renderer=None):
    raw, state, brief = state_data(project)
    cards = []
    inputs = hashes({STATE: raw})
    for hypothesis in state["hypotheses"]:
        key = hypothesis["id"]
        if key in state["candidates"]:
            _, masters, files = proof_packet(project, key, state["candidates"][key], state, brief)
            inputs[key] = digest(files[PACKET])
            cards.append((hypothesis, masters["mark"], state["grounds"]["light"]))
    return packet_files("comparison", inputs, {"comparison": studio.comparison(brief["name"], cards)},
                        {"shortlist.json": raw}, renderer)


def application_inputs(masters, state, brief):
    return hashes({**{f"{key}.svg": data for key, data in masters.items()},
                   "context.json": json_bytes({"grounds": state["grounds"],
                                               "applications": state["applications"],
                                               "name": brief["name"]})})


def applications(project, candidate, renderer=None):
    _, state, brief = state_data(project)
    require(candidate in state["candidates"], f"Unknown candidate: {candidate}")
    _, masters, _ = proof_packet(project, candidate, state["candidates"][candidate], state, brief)
    require(masters.keys() == set(MASTERS), "Application studies require mark, horizontal and stacked masters")
    return packet_files("applications", application_inputs(masters, state, brief),
                        {"applications": studio.applications(brief["name"], masters, state["grounds"],
                                                             state["applications"])}, renderer=renderer)


def reviewed_round(project, candidate, revision, state, brief):
    directory, masters, proof = proof_packet(project, candidate, revision, state, brief)
    inspection = project_file(directory / "inspection.json")
    record = validate("creative-inspection", inspection)
    require(record["packet_sha256"] == digest(proof[PACKET]), f"Inspection does not match render of r{revision}")
    evidence = {**{f"proof/{name}": data for name, data in proof.items()},
                **{f"{name}.svg": data for name, data in masters.items()},
                "iteration.json": project_file(directory / "iteration.json"),
                "inspection.json": inspection}
    return masters, proof, record, evidence


def release_inputs(project, candidate, concept):
    raw, state, brief = state_data(project)
    require(candidate in state["candidates"], "Approved concept must be a shortlisted candidate")
    active = state["candidates"][candidate]
    require(active >= 2, "Creative delivery requires an inspected refinement and re-render")
    board, packet = verify_packet(project / "creative" / "comparison", "comparison",
                                  sheet_names(("comparison",)) | {"shortlist.json"})
    selection = f"comparison-sha256 {digest(board[PACKET])}"
    require(selection in concept["provenance"], "Approved concept must cite the exact comparison packet")
    snapshot = validate("creative-state", board["shortlist.json"])
    require(snapshot["brief_sha256"] == state["brief_sha256"] and candidate in snapshot["candidates"] and
            packet["inputs"].get(STATE) == digest(board["shortlist.json"]),
            "Comparison does not cover the approved brief and candidate")
    selected_round = snapshot["candidates"][candidate]
    require(selected_round <= active, "Selected comparison round is newer than the active round")
    files = {STATE: raw, **{f"creative/comparison/{name}": data for name, data in board.items()}}
    previous = None
    critiqued = False
    for revision in range(1, active + 1):
        masters, proof, review, evidence = reviewed_round(project, candidate, revision, state, brief)
        if revision == selected_round:
            require(packet["inputs"].get(candidate) == digest(proof[PACKET]),
                    "Selected round differs from approved comparison")
        geometry = {name: canonicalize(data.decode("utf-8"), strip_text=True) for name, data in masters.items()}
        if previous is not None:
            require(geometry != previous, f"No SVG change in refinement r{revision}")
        previous = geometry
        if revision < active and review["decision"] == "refine":
            critiqued = True
        files.update({f"creative/{candidate}/r{revision}/{name}": data for name, data in evidence.items()})
    require(critiqued, "Record at least one prior critique that calls for refinement")
    require(review["decision"] == "ready", "Current visual inspection must mark this round ready")
    require(masters.keys() == set(MASTERS), "Creative delivery requires mark, horizontal and stacked masters")
    apps, _ = verify_packet(project / "creative" / "applications", "applications",
                            sheet_names(("applications",)), application_inputs(masters, state, brief))
    files.update({f"creative/applications/{name}": data for name, data in apps.items()})
    return masters, files
