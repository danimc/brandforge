# Brandforge

Brandforge is a Codex Agent Skill for developing a cohesive identity and releasing a verified brand kit. It compares original creative directions before assembling editable SVG variants, web tokens, brand guidelines and print specifications.

## Use in Codex

Place this directory at `.agents/skills/brandforge` in the workspace. Invoke `$brandforge` with the brand’s audience, offer, constraints and priority applications. The agent asks for concept selection and final delivery approval at separate checkpoints. [Skill entrypoint](SKILL.md) · [Architecture and plan](PLAN.md) · [Upstream comparison and reuse](references/research.md)

Use Python 3.9 or later. The CLI and tests use only the standard library. The checks were run on Python 3.9.6 and 3.13.11. The demo review used librsvg 2.62.1 and Cairo 1.18.4. The bundled skill-creator validator ran separately with PyYAML 6.0.3.

## Reproduce the fictional kit

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

## Adapt to a new project

1. Follow the [deliverable contract](references/deliverables.md) and the JSON Schemas in `schemas/`.
2. Run `fingerprint FILE` for the brief and selected board. Save their digests with the explicit concept decision. Preserve superseded brand spec revisions.
3. Use `svg FILE` and `contrast FILE` for early diagnostics. Contrast prints results and exits nonzero if any pair fails.
4. Run `build PROJECT REVIEW_DIR` to assemble the mark and lockup in primary, black and reverse, plus brief, concept, review spec, tokens, CSS, contrast results, guidelines and print notes. Build into a fresh directory whose parent exists. Inspect rendered work and rebuild if anything changes.
5. Run `verify REVIEW_DIR` and present the review with its manifest fingerprint. After explicit final approval, save the next spec revision with the same reviewed decisions and final approval pointing at that digest. Run `release REVIEW_DIR APPROVED_SPEC FINAL_DIR`, then `verify FINAL_DIR --released`. Release copies the exact reviewed bytes to a fresh directory and adds the approval receipt.

## Verification boundaries

Manifest checks establish integrity relative to the fingerprint supplied at review. Keep that fingerprint with the approval record. The manifest and receipt are unsigned, and the tool relies on the agent to record real approvals accurately. Use a local workspace under your control during build and release.

Automated SVG validation covers a restricted static profile. Visual bounds, optical balance, originality and trademark availability require separate review. Contrast checks cover declared opaque pairs. In-context accessibility, font coverage and font rights require separate review. Printer profiles, proofs, PDF/X and native Illustrator files are outside the offline MVP. [Optional integrations](references/integrations.md)
