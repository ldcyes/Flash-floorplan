# Flash-flooplanner Pixel Edition 8.6.1

Interactive early-stage IC architecture exploration with process scaling, SRAM-aware sizing, metal-aware routing pressure, W2W yield/cost, first-class connection management, and topology comparison.

- Planner: https://ldcyes.github.io/Flash-floorplan/
- Compatibility entry: https://ldcyes.github.io/Flash-floorplan/planner.html
- Updated preprint PDF: https://ldcyes.github.io/Flash-floorplan/paper.pdf
- Paper source: `paper/v8.6.1/`

## v8.6.1 highlights

- CPU templates: Arm Cortex-A55, Cortex-A76, Cortex-R82, BOOM, XiangShan, Arm C1-Ultra, NVIDIA Vera Olympus, and Tenstorrent RISC-V Ocelot.
- Tenstorrent Wormhole and Blackhole are removed from the selectable template library. Legacy projects are preserved as fixed custom geometry when possible.
- Persistent connection list with edge-anchored orthogonal buses.
- Per-net horizontal/vertical metal-layer allocation and corridor-width estimation.
- `P` Place-wire shortcut, Space / Shift+Space 90-degree module rotation, undo/redo integration.
- Flat Crossbar / Hierarchical Crossbar / Beneš / Mesh / Ring comparison and partition objective.
- Google Drive import/save UI is removed; projects remain local-first through JSON and drawing exports.
- Pixel-only product styling.

## Paper and validation

The v8.6.1 preprint separates measured/calibrated/estimated/heuristic evidence and includes a redrawn architecture figure with dedicated connector gutters and a separate feedback lane to prevent arrows or labels from overlapping boxes.

The retained Nangate45/OpenROAD validation reports 24.87% held-out area MAPE; the experimental MST + segment-union routing proxy improves mean Pearson congestion correlation from 0.430 to 0.737. These results validate a narrow proxy task and must not be interpreted as signoff accuracy across advanced process nodes.

## Pages build

GitHub Pages reconstructs the v8.6 source release, applies the v8.6.1 retirement patch, removes the Drive UI, verifies release markers, and publishes a full standalone planner. The workflow also compiles `paper/v8.6.1/main.tex` and exposes the PDF as `/paper.pdf`.

Author: Liangdacheng with GPT5.5. MIT License. The paper is a preprint; publishing it here does not constitute an arXiv submission.
