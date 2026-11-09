# Creative Engine architecture

The host agent authors the brief interpretation, research and visual work. The local CLI takes typed project inputs and checks the resulting evidence. Each component owns a distinct stage.

| Component | Inputs | Outputs |
| --- | --- | --- |
| Concept Exploration | Brief, category research and optional raster provenance | `creative.json`, 8–12 hypotheses, reasons for 3–6 shortlisted candidates |
| SVG Craft | Candidate idea, licensed type or original lettering, role colors | Editable round masters, provenance and design changes |
| Visual Evaluation | One round’s static SVGs, a light and dark ground | Technical JSON and rendered proof packets, followed by an explicit inspection record |
| Presentation Studio | Shortlist proofs and application copy | Editorial comparison and digital/print study as SVG and PNG |

`creative.py` resolves stage inputs and verifies hashes. `studio.py` composes generated SVG sheets. `renderer.py` passes them through local librsvg. `image_input.py` imports raster provenance independently of the image provider. `brandforge.py` assembles the kit using the established contrast, manifest and approval machinery. None of these commands sends network requests.

## State transitions

1. Author the hypotheses and create r1 for each shortlisted ID. A render command takes one ID and an optional historical round. It writes into a new directory and leaves other candidates alone.
2. Create the comparison packet with an immutable shortlist snapshot and source proof digests. Ask the user to choose a direction and bind the concept approval to that packet. Later refinements keep the approved comparison frozen.
3. Inspect the selected round, record a critique tied to its proof digest, then create and inspect a later round. The build requires a concrete canonical SVG difference, a prior refinement decision, a current ready record and all three masters. Build the application study from the latest masters and intended context.
4. Freeze and verify the review manifest. Capture approval of that digest, then release exact reviewed bytes with the next brand-spec revision.

The current state is additive to the 1.0 brief, concept, spec and output manifest. The decision history lives in round directories and spec revisions. The packet hashes detect accidental staleness and tampering relative to a trusted approval reference. They are unsigned. Keep these files in a controlled project. A tool can check the existence and integrity of a reviewer statement. A reviewer must actually inspect the render.

The renderer and local font stack affect pixel output. Build and release consume committed packets without requiring the renderer and reproduce exact reviewed bytes. The static SVG profile excludes external references and raster content in masters. Rendered sheets are presentation artifacts and have a wider layout syntax than the master profile.
