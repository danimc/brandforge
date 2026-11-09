---
name: brandforge
description: Design or refresh a brand identity from a brief through strategy, concept selection, original editable SVG marks, typography, accessible color roles, and a validated brand kit. Use when a user wants a logo and supporting identity system, brand guidelines, or production handoff assets.
metadata:
  version: "1.0.0"
---

# Brandforge

1. **Brief.** Read [strategy](references/brand-strategy.md). Create a project folder with `brief.json` and a revisioned `brand-spec.json` using the [contracts](references/deliverables.md). Reopen the files on resume and check the current approval scope.
2. **Directions.** Read [creative direction](references/creative-direction.md). Present distinct directions with rationale, strengths, tradeoffs and differentiation evidence. Persist the options. Stop for explicit selection of a concept ID and record the response with the input fingerprints. Never trace or imitate an existing mark. Redesign if resemblance is material.
3. **Build.** Apply [SVG design](references/svg-design.md), [typography](references/typography.md), [color](references/color.md), and [accessibility](references/accessibility.md). Create editable masters, tokens, guidelines and print specifications. Use [optional integrations](references/integrations.md) when appropriate.
4. **Review.** Build a review kit with `scripts/brandforge.py build`. Verify it, render the marks at intended sizes and inspect all variants, verify type and usage rights, and record checks and open issues in the review files. Rebuild in a fresh directory after changes. Present the exact kit and manifest fingerprint, then stop for explicit final delivery approval.
5. **Deliver.** Record the approval in the next spec revision. Release only the approved review bytes with `release` and verify with `verify --released`. Provide the verified kit, editable masters, guidelines, and any outstanding production conditions.

Preserve prior spec revisions in the project. Changes to the brief or selected board require a new concept decision. Changes to review bytes require new final approval. Never manufacture approval or treat a tool pass as trademark clearance. The fictional example contains simulated approvals for tests only.
