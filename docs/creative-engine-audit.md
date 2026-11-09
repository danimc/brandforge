# Creative Engine audit

Baseline: Brandforge 1.0.1, commit `29e2759`. The four upstream default-branch heads were rechecked on 2026-11-08 and matched the pinned snapshots in the [reuse matrix](../references/research.md). Inspection was read-only. No upstream scripts, installers or generation services were run.

## Baseline and causes

The brief, concept and release fingerprints already protect decisions against accidental drift. The SVG parser already accepts cubic and quadratic Béziers, closed compound paths and even-odd knockouts. It checks syntax and safety. The build derives monochrome SVGs, audits declared sRGB pairs and verifies kit hashes.

Creative direction requested two or three directions and left exploration, comparative presentation and iteration to the agent. The example developed one split-folio mark, with one simpler alternate. The deliverable contract had no shortlist, iteration chain or render-bound evidence. A nonempty review Markdown file was enough to build. The CLI could preserve a polished vector if supplied, but its demonstration and feedback loop gave the agent little reason to test a second composition, refine curves or tune an optical gap.

## What the upstream implementations do

| Source | Executable capabilities inspected | Guidance, dependency or evaluation boundary |
| --- | --- | --- |
| [kaankiziltug](https://github.com/kaankiziltug/logo-design-skill/tree/bbf31e521d765eb6d53242549bbee7c2e5bbd6bc) | `svglib.py` parses geometry and transforms. `svg_audit.py` reports bounds, paint and geometry properties. `concept_sheet.py` builds a sheet, `presentation_board.py` implements HTML application templates, and `export_variants.py` builds recolored and wrapped variants. `render_png.py` has several optional native/browser render backends. | Construction, critique and testing references direct the agent’s optical work. Geometry and reference matches do not judge originality. Trademark assets are expressly excluded from MIT. |
| [op7418](https://github.com/op7418/logo-generator-skill/tree/bf4e9ac4d4428bda261afcfe981871ceb92d94e6) | `svg_to_png.py` calls CairoSVG. `generate_showcase.py` optionally encodes an input image and calls Gemini via `client.models.generate_content`; it reads its API key from the environment. | The pattern and background references guide authoring and prompting. The showcase is generated imagery, with no deterministic fidelity check or vector conversion. The README declares MIT and the pinned tree has no standalone license file. |
| [SanbaoAI](https://github.com/SanbaoAI/logo-generator-skill/tree/d62b0e2a52251e39a4ad7a376bf35675cc967753) | The Bash selector maps names to three skill paths. The skills supply prompts, input schemas and example images for base, mascot and colorway work. | Instructions delegate generation to the host and can return a prompt. The tree supplies no native vector build or pixel QA implementation. Root MIT does not establish rights to depict a third-party mark. |
| [fatihaydost](https://github.com/fatihaydost/brand-identity-skill/tree/3ba008e57b9363cf2a9117303237f951a7c1ef00) | `pipeline.py` builds coordinated identity sets. `logolib.py` shapes type using HarfBuzz and uses path operations. `logo_audit.py` measures thin features and adjacency. Palette, font, card, token and kit scripts implement separate checks and outputs. | FontTools, uharfbuzz and skia-pathops provide measurement and shaping. Browser preview adds a presentation dependency. Cohesion and competitor heuristics cannot establish distinctiveness or clearance. MIT and separate third-party notices govern reuse. |

Brandforge adopts the workflows of comparing coherent directions, inspecting the actual render, and separating clean proof sheets from showcases. It incorporates no upstream code, prompts, data, fonts or artwork.

## Decisions

- Keep the existing editable SVG profile and approved delivery contracts. Add a third, stacked master in creative projects and preserve the existing exports byte-for-byte for legacy projects.
- Keep creative judgment with the host and user. Make candidate history, rendered evidence and visual observations structured and inspectable. Avoid numerical taste scores.
- Use a local renderer behind an adapter. Compose original vector presentations from validated inputs. Keep network image generation optional and separate from geometry and review.
- Bind review packets to assets and approval receipts through hashes. Record authorship and reviewer statements explicitly. SHA-256 tracks bytes and does not authenticate a reviewer.
