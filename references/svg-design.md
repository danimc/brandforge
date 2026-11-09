# Editable SVG construction

Design in a single color before adding palette roles. Resolve optical weight, counters, spacing and alignment across symbol and lockup. Make knockout areas actual cutouts so variants survive recoloring. Preserve editable geometry and turn wordmark glyphs into paths with appropriate rights.

The offline export profile accepts UTF-8 SVG with a positive viewBox, unstyled groups, and solid-filled paths, polygons, rectangles and circles. Use explicit per-shape six-digit hex fills or `none`, optional fill-rule, absolute space-separated M/L/C/Q/Z path commands with a closed subpath, and space-separated numeric coordinates. Flatten transforms and expand strokes. Use one regular root SVG element with no dimensions, text, external references, filters, style, comments or declarations. Inspect results for degeneracy, clipping, unintended overlaps and negative-space loss. The parser checks structure and syntax. It cannot establish optical quality or visual bounds.

The tool preserves primary artwork bytes and derives black and white versions by recoloring painted geometry. A logo that depends on hue to separate touching forms needs a manually refined geometry before this derivation is suitable.

## Creative rounds

Create a new `creative/<candidate>/rN/` folder for each refinement. Keep `mark.svg` as the clean candidate silhouette. Add `lockup.svg` and `stacked.svg` for the horizontal and vertical compositions. A shortlist proof may begin with the mark. All three masters are required for delivery.

Use C and Q commands for flowing silhouettes and custom lettering. Shape counters and open spaces before selecting color. Test whether curves retain a coherent tangent and whether negative space closes at the most constrained size. Compare the mark’s apparent weight with the wordmark. Adjust tracking, overshoot, alignment and clear space optically. Normalize SVG geometry before export so it stays editable in common vector editors.

When converting installed or supplied type to outlines, verify the actual family’s license for the intended use, and record the source and permission. Hand-drawn lettering remains an option. Inspect both reading direction and kerning at use size. Record applications where the isolated wordmark or full lockup can work, and where the mark alone is required.
