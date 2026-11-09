# Project and delivery contract

Use the [schemas](../schemas/) for `brief.json` (brand-brief), each `concepts/<id>.json` (concept), `tokens.json` (design-tokens), `brand-spec.json` (brand-spec), and the generated manifest (output-manifest). Store brand spec snapshots in a revision directory or Git. Start with schema version, revision and brief digest. Add the concept ID, board digest and approval as a group when approved. Store important board choices in the concept record so the hash covers the presented direction. Keep linked visual previews in the versioned project and record their digests in the concept provenance when used for approval.

An approval contains a person, ISO calendar date, evidence reference, and simulated flag. Use an explicit user response in real work and record a short reference, avoiding unnecessary private data. Hash the exact bytes via `fingerprint`. The review spec and release spec represent consecutive revisions. Final approval includes the review manifest hash. A final kit includes that exact manifest, reviewed files and the new release spec as an approval receipt.

Required design inputs are `source/mark.svg`, `source/lockup.svg`, `guidelines.md`, `print.md` and `visual-review.md`. Guidelines cover the strategy, artwork usage, minimum sizes, clear space, typography, color roles, visual language, examples and misuse. Print notes document target production conditions and open checks. See the [fictional project](../examples/veskil/).

## Creative projects (0.2)

Add `creative.json` using the creative-state schema. Keep the original brief. Store each shortlisted direction at `creative/<id>/rN/` with `iteration.json`, editable SVGs, a `proof/` packet and, for reviewed rounds, `inspection.json`. Keep historic rounds intact. Start candidates at r1. Increase only the candidate being refined. The state contains the full hypothesis set, shortlist decisions, provenance, mode, grounds and copy for the application studies.

Generate the initial atlas in `creative/comparison/`. For direction approval, write the chosen direction's legacy concept record with a provenance entry in the form `comparison-sha256 <packet digest>`. This binds the existing approved concept hash to the exact comparison and its frozen shortlist. Create later rounds outside that snapshot. After visual review, build the chosen direction’s current context sheet into `creative/applications/`.

`build` detects the creative project and requires the approved board, the chosen round history with inspections, a reviewed refinement, the three editable masters and matching context studies. The resulting review kit includes the comparison, selected proof history, provenance, context studies and nine logo SVGs. The existing final approval process binds the entire review manifest. For changes after review, regenerate the affected packets in fresh paths before replacing the project references or creating a new review version.

Existing projects without `creative.json` build with their existing inputs, manifests and approvals. Migrating a project to creative mode is opt-in. Preserve the original brief and historical specs. Create the new state and rounds, then ask for selection of the newly presented board. Keep the earlier released kit as a separate release. No rewriting of old approvals is required.
