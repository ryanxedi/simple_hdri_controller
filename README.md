# Simple HDRI Controller (Blender Add-on)

A tiny Blender add-on that lets you **load an HDRI** and **rotate it** from a simple **N‑panel**. No Shader Editor or node wrangling. Pick an HDRI (`.hdr`/`.exr`), adjust rotation and strength, and get on with lighting.

## ✨ Features
- **N‑panel UI**: 3D Viewport → press **N** → **HDRI** tab.
- **Load HDRIs** with a file picker or by dropping an image onto the slot.
- **Rotate** environment (Z‑axis) with a single control.
- **Strength** slider for background brightness.
- **Reset** button (rotation = 0, strength = 1.0).
- **Auto node setup**: creates a tidy World node tree if you don’t have one.

## Requirements
- **Blender 3.0+** (tested on 3.x–4.x)
- HDRI files: `.hdr` or `.exr`

## Installation
1. Download `simple_hdri_controller.py`.
2. In Blender: **Edit → Preferences → Add-ons → Install…**
3. Select the file and **Enable** the add-on.

> Tip: keep the file in your repo and reinstall directly from there when you update.

## Quick Start
1. Open the **3D Viewport**, press **N**, go to the **HDRI** tab.
2. Click **Load HDRI** and choose a `.hdr`/`.exr`, **or** drag an HDRI onto the **HDRI** image slot.
3. Use **Rotation** to spin the lighting; **Strength** to adjust intensity.
4. Hit **Reset** to go back to defaults.

## How It Works (under the bonnet)
On first use, the add-on ensures your World has this minimal graph:

```
Texture Coordinate → Mapping → Environment Texture → Background → World Output
                                (Z rotation)
```

- Rotation control maps to the **Mapping** node’s **Z** rotation.
- Strength maps to the **Background** node’s **Strength**.

## Drag & Drop Notes
- Blender lets you drop images from the **File Browser** onto the **image ID field** in the panel.
- Dropping a `.hdr/.exr` there will **load and apply** it immediately.

## Troubleshooting

### Background looks black / no lighting
- Use **Rendered** view (Eevee or Cycles).
- Confirm the HDRI is loaded (its name appears in the **HDRI** slot).
- In Cycles with Film **Transparent**, you still get lighting but no visible background.

## Roadmap
- [ ] **Transparent background** toggle (keep lighting, hide background).
- [ ] **Flip/Invert** convenience toggle.
- [ ] Optional **separate strength** for camera vs. environment lighting.
- [ ] Per‑scene preset save/load.

## Contributing
PRs and issues welcome. Please:
- Keep the UI simple and non‑destructive.
- Avoid touching scene/world during `register()` (prevents restricted‑context errors).
- Stick to Blender’s Python API conventions.

## Version History
- **1.0.2** – Correct rotation application (no double radians); polish.
- **1.0.1** – Safer context handling; no scene access during `register()`.
- **1.0.0** – Initial release (load HDRI, rotate, strength, reset, auto node setup).

## Licence
MIT is a good fit for a small utility add‑on. Add a `LICENSE` file with:

```
MIT License

Copyright (c) 2025 <Your Name>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
```


---
