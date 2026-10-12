# Architecture assets

| File | Scope |
| --- | --- |
| `architecture.png` / `.svg` / `.drawio` | Proposed AWS deployment using service icons and network boundaries |
| `implementation.png` / `.svg` / `.drawio` | Components actually present in the runnable release |
| `layers.png` / `.svg` / `.drawio` | Detailed domain, application and adapter boundaries |
| `workbench.png` | Screenshot of the running local application |

The diagrams are precise code-generated vector drawings with orthogonal labeled connectors. The diagrams.net files contain editable groups, text, service images and anchored connectors. They are not screenshots inside a single shape. Icons are embedded so editing does not need remote image hosts.

From the repository root, regenerate the icon-based SVG and drawio files with:

```bash
python scripts/render_architecture.py
```

Regenerate the detailed layer view with `python scripts/render_layers.py`. These scripts use only the Python standard library. Export a regenerated SVG to PNG with an SVG renderer, or open the corresponding `.drawio` file in diagrams.net and export PNG at 2400 px width on a white background. PNGs are committed for reliable GitHub README rendering.

See [icon notices](icons/ATTRIBUTION.md). AWS diagrams are a deployment proposal; the local application does not provision AWS services.
