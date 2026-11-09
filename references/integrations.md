# Optional integrations

Use an available image generation tool for mood explorations, storyboards or contextual mockups. Obtain authorization for any external upload that needs it. Use only authorized references, retain provenance and provider terms, and label previews as illustrative. Construct the master separately as original editable geometry.

For Illustrator, open the editable SVG, check paths and knockouts, and save a separate .ai working file if required. Ask the printer for the requested PDF/X preset and ICC output intent, then proof the result with the vendor. If vector masters return from Illustrator, flatten transforms and normalize to the Brandforge SVG profile before rebuilding and reapproving. [Adobe Illustrator save formats](https://helpx.adobe.com/illustrator/using/saving-artwork.html)

The core build uses no provider or Adobe credentials. Optional tools run outside the CLI. Record their exact versions, provenance and export settings when used.

## Creative engine adapters

The host owns provider choice, permissions, prompts and credentials. Use a configured image tool only when it serves the brief. Export PNG or JPEG to the project, then run `image-reference FILE --provider NAME --observation NOTES --rights TERMS`. The command emits a provenance object for `creative.json`. It accepts local regular raster files, checks the file signature and records the basename and SHA-256. It does not decode images, call providers or read API credentials. Keep private prompts and provider credentials out of published project files. For hybrid work, inspect and abstract the idea, reconstruct native paths, and test the resulting clean vector independently.

`renderer.py` adapts local librsvg. It renders generated sheets from approved SVG-profile input, uses an argument list and timeout, and records the backend version. Install librsvg using your host's trusted package manager when you need new renders. Keep font and renderer versions fixed when reproducing pixel-identical evidence.
