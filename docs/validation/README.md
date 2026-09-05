# Executed Nangate45 validation pilot

Source commit: `194ab85fd1f6058b772fe9a7daa4d1fe882068b2`.
Primary run: https://github.com/ldcyes/Flash-floorplan/actions/runs/33963302104
Raw artifact: `9969093457`. SHA256: `c2030472783064f6013de4edd801fa37ff264ecd73bd4b0176a77c7bb7ace5e5`.

All 18 RTL designs completed simulation, synthesis and placement. 33/36 route scenarios completed; three 300-second OpenROAD process timeouts are retained. Workflow failure is intentional when route cases fail. Completed global routing does not imply zero overflow.

## Held-out mapped-cell area

Each family has two calibration designs and four test designs. No test area enters scalar fitting.

| Family | Test n | MAPE (%) | Max APE (%) |
|---|---:|---:|---:|
| crossbar | 4 | 32.1074 | 49.6239 |
| benes | 4 | 16.1228 | 22.3232 |
| router | 4 | 26.3820 | 45.4111 |
| all | 12 | 24.8708 | 49.6239 |

## Held-out post-placement routing adapter

Known placed pins and characterized resource supply; not a full no-RTL placement or multi-foundry validation. Hotspot threshold is projected H/V pressure >=0.8. v6 driver-star/tile and experimental MST/segment-union are reported separately.

| Method/budget | Maps | Mean Pearson | Mean Spearman | Pooled F1 | Kernel median (ms) |
|---|---:|---:|---:|---:|---:|
| legacy_star_tile/nominal | 11 | 0.4905 | 0.6913 | 0.7626 | 3.1683 |
| legacy_star_tile/constrained | 10 | 0.3632 | 0.5519 | 0.8854 | 2.7869 |
| legacy_star_tile/all | 21 | 0.4299 | 0.6249 | 0.8077 | 3.0139 |
| mst_union_edge/nominal | 11 | 0.8238 | 0.8448 | 0.7964 | 9.3497 |
| mst_union_edge/constrained | 10 | 0.6426 | 0.6858 | 0.8463 | 9.4326 |
| mst_union_edge/all | 21 | 0.7375 | 0.7690 | 0.8179 | 9.3497 |

**F1 caveat:** constrained maps are overwhelmingly positive; compare an always-hot baseline and inspect per-map support/TP/FP/FN/TN. High pooled F1 alone does not establish hotspot localization. Kernel timing excludes synthesis, placement, I/O and process startup.

## Failed route scenarios

- `router_n16_w8 / constrained`: Command '['openroad', '-exit', 'constrained.tcl']' timed out after 299.99998474200015 seconds
- `router_n16_w16 / nominal`: Command '['openroad', '-exit', 'nominal.tcl']' timed out after 299.99998591300005 seconds
- `router_n16_w16 / constrained`: Command '['openroad', '-exit', 'constrained.tcl']' timed out after 299.99998462099984 seconds

## Measurement boundaries

One public Nangate45 typical library; no commercial 28nm-to-2nm, compiled SRAM/PHY, W2W yield/cost, timing, power or detailed-routing validation. Resource-only occupancy is subtracted from routed usage before treating it as signal demand.
See JSON for complete runtime distributions, masks, missing-case accounting and per-map metrics. Raw RTL/netlist/LEF/Liberty/ODB/DEF/guide/log evidence remains attached to the primary run.
