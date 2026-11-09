# Brandforge

Brandforge is a Codex Agent Skill for developing a cohesive identity and releasing a verified brand kit. It researches and explores several directions, renders and inspects real artwork, then assembles editable vectors, web tokens, brand guidelines and print specifications.

## Install and invoke

Copy the whole Brandforge directory to the host’s skill directory. The destination folder must be named `brandforge` and contain `SKILL.md` directly. Copy the scripts, schemas and references alongside it.

| Host | Global install path | Invoke |
| --- | --- | --- |
| Codex | `~/.agents/skills/brandforge` | `$brandforge` |
| Claude Code | `~/.claude/skills/brandforge` | `/brandforge` |
| Google Antigravity App, CLI and IDE | `~/.gemini/config/skills/brandforge` | `/brandforge` in the App or CLI. In the IDE, check Customizations and ask for Brandforge by name. |

Open a fresh session after installing. Refresh installed copies from the repository when upgrading. For project-scoped installs, place the folder under `.agents/skills/` for Codex and Antigravity or `.claude/skills/` for Claude Code. The Claude Code instructions are for local sessions. Claude Cowork and cloud sessions manage account skills separately. [Claude Code skill docs](https://code.claude.com/docs/en/skills) · [Antigravity skill docs](https://antigravity.google/docs/skills?app=antigravity)

Start with the brand’s audience, offer, constraints and priority applications. Brandforge asks for concept selection and final delivery approval at separate checkpoints. [Skill entrypoint](SKILL.md) · [Architecture and plan](PLAN.md) · [Upstream comparison and reuse](references/research.md)

Use Python 3.9 or later. The CLI uses only the standard library. To create new PNG proofs and boards, install librsvg so `rsvg-convert` is on PATH. Building and verifying already rendered projects works offline without librsvg. The checks were run on Python 3.9.6 and 3.13.11. The demo review used librsvg 2.62.1 and Cairo 1.18.4. The bundled skill-creator validator ran separately with PyYAML 6.0.3.

## Creative Engine

Try “Create an identity for a field notebook brand,” “Explore more directions,” “Refine the third proposal,” or “Show the logo on a catalog tile and a card.” Start with the [skill](SKILL.md) and follow the [creative project contract](references/deliverables.md#creative-projects-02).

A typical project keeps the shortlist in `creative.json` and the artworks in `creative/<id>/rN/`. Run these commands from the skill directory, substituting your project path and ID. The output parents must exist and the target directories must be new.

```sh
python3 -B scripts/brandforge.py render PROJECT ID PROJECT/creative/ID/r1/proof
# Repeat the render for each shortlisted direction.
python3 -B scripts/brandforge.py present PROJECT PROJECT/creative/comparison
# Stop for direction approval. Inspect, critique, and edit in a new round.
python3 -B scripts/brandforge.py render PROJECT ID --round 2 PROJECT/creative/ID/r2/proof
python3 -B scripts/brandforge.py applications PROJECT ID PROJECT/creative/applications
python3 -B scripts/brandforge.py build PROJECT REVIEW_DIR
python3 -B scripts/brandforge.py verify REVIEW_DIR
# Stop for explicit approval of the review manifest.
python3 -B scripts/brandforge.py release REVIEW_DIR APPROVED_SPEC FINAL_DIR
python3 -B scripts/brandforge.py verify FINAL_DIR --released
```

After inspecting each selected-round PNG, write its inspection record. See the [Veskil creative project](examples/veskil-creative/) for the contract in use, with simulated approvals. A provider is optional. The [raster intake](references/integrations.md#creative-engine-adapters) records references without sending the files to a service.

### Curated logo library

BrandForge includes four original Veskil references. You can keep your own portable catalog, import assets you own or have verified permission to store, and add third-party marks as link-only entries. Filter by industry, mark type and technique. [Library guide](references/reference-library.md)

### Rebuild the creative benchmark kit

```sh
work="$(mktemp -d)"
python3 -B scripts/brandforge.py build examples/veskil-creative "$work/review"
cmp examples/veskil-creative/expected-manifest.json "$work/review/manifest.json"
python3 -B scripts/brandforge.py release "$work/review" examples/veskil-creative/revisions/003.json "$work/final"
python3 -B scripts/brandforge.py verify "$work/final" --released
python3 -B -m unittest discover -s tests -v
```

Review, release and verify use fingerprint `f451d0361e3990e47d397c49cb0eea2109954dc447ad37a8ea1ded117fc0f305`. The committed render packets are inputs to this reproducibility check. Re-rendering on a different environment can change the hash. [Benchmark](docs/creative-engine-benchmark.md) · [Audit](docs/creative-engine-audit.md) · [Architecture](docs/creative-engine-architecture.md) · [Changelog](CHANGELOG.md)

## Reproduce the baseline kit

Run from this directory. Veskil’s approvals are simulated. Its `brand-spec.json` is the frozen review-stage spec.

```sh
work="$(mktemp -d)"
python3 -B scripts/brandforge.py build examples/veskil "$work/review"
python3 -B scripts/brandforge.py verify "$work/review"
python3 -B scripts/brandforge.py release "$work/review" examples/veskil/revisions/003.json "$work/final"
python3 -B scripts/brandforge.py verify "$work/final" --released
python3 -B -m unittest discover -s tests -v
```

All four kit commands should print `bc14b4f91eacab00bfa97e1ea40264e4ac17c54cad281b7904d72a467c3e0897` for the supplied inputs. [Demo project](examples/veskil/) · [Rendered contact sheet](examples/veskil/preview.png) · [Released demo](examples/veskil-kit/)

## Continue a legacy project

1. Follow the [deliverable contract](references/deliverables.md) and the JSON Schemas in `schemas/`.
2. Run `fingerprint FILE` for the brief and selected board. Save their digests with the explicit concept decision. Preserve superseded brand spec revisions.
3. Use `svg FILE` and `contrast FILE` for early diagnostics. Contrast prints results and exits nonzero if any pair fails.
4. Run `build PROJECT REVIEW_DIR` to assemble the mark and lockup in primary, black and reverse, plus brief, concept, review spec, tokens, CSS, contrast results, guidelines and print notes. Build into a fresh directory whose parent exists. Inspect rendered work and rebuild if anything changes.
5. Run `verify REVIEW_DIR` and present the review with its manifest fingerprint. After explicit final approval, save the next spec revision with the same reviewed decisions and final approval pointing at that digest. Run `release REVIEW_DIR APPROVED_SPEC FINAL_DIR`, then `verify FINAL_DIR --released`. Release copies the exact reviewed bytes to a fresh directory and adds the approval receipt.

## Verification boundaries

Manifest checks establish integrity relative to the fingerprint supplied at review. Keep that fingerprint with the approval record. The manifest and receipt are unsigned, and the tool relies on the agent to record real approvals accurately. Use a local workspace under your control during build and release.

Automated SVG validation covers a restricted static profile. Visual bounds, optical balance, originality and trademark availability require separate review. Contrast checks cover declared opaque pairs. In-context accessibility, font coverage and font rights require separate review. Printer profiles, proofs, PDF/X and native Illustrator files are outside the offline MVP. [Optional integrations](references/integrations.md)
