# Curated reference library

Search the [Veskil sample catalog](../examples/reference-library/) or point the CLI at a folder you maintain. Keep a personal or shared catalog outside the skill folder so upgrades preserve it. A catalog is portable across computers. Sync its whole folder according to the rights recorded for each asset.

```sh
python3 -B scripts/brandforge.py library-search examples/reference-library --technique negative-space
python3 -B scripts/brandforge.py library-search examples/reference-library --industry stationery --mark-type monogram
python3 -B scripts/brandforge.py library-reference examples/reference-library veskil-transect
python3 -B scripts/brandforge.py library-add /path/to/catalog card.json --asset mark.svg
```

Use the [card schema](../schemas/library-card.schema.json) and the field names below. Classify logos with stable kebab-case labels, such as `stationery`, `monogram`, `negative-space` and `custom-lettering`.

| Field | What to record |
| --- | --- |
| `id`, `title` | Stable slug and display name. A duplicate slug cannot overwrite an entry. |
| `industry`, `mark_type`, `techniques` | Search labels that describe the reference. |
| `source`, `rights` | Original source and a note about authorship, license or storage permission. Include the license source and conditions when applicable. |
| `observation` | A specific principle to study, such as how the silhouette retains a counter at small sizes. |
| `storage` | `owned` or `licensed` with a local asset, or `link-only` with a public HTTPS URL. |

For a link-only entry, omit `--asset`. Use a public URL without credentials or query parameters. The tool stores the link and does not fetch it. For an owned or licensed entry, use a safe-profile SVG, PNG or JPEG. SVGs use BrandForge’s strict editable profile. The importer copies raster bytes as-is, so remove sensitive metadata before sharing. A declared storage policy records your decision about permission. BrandForge does not verify legal rights.

`library-search` returns JSON cards. `library-reference` verifies a copied asset’s SHA-256 and emits a record for the `references` array in `creative.json`. Inspect the relevant visual yourself before citing it. Use the catalog to study principles and document differences. Keep recognizable third-party artwork out of new concepts and deliverables.
