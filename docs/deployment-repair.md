# Pixel v8.3 Pages deployment repair

## Incident

Pages run 34127298154 failed during static-site preparation with `xz: (stdin): Unexpected end of input`. Only the first compressed fragment had been committed. The workflow also omitted the legacy `/planner.html` entry. A successful Git push had incorrectly been treated as evidence of deployment.

## Repair

The exact previously delivered Pixel v8.3 application was recovered and verified against SHA-256 `65a187941021feef7c81970b63915317e7be9192630205d8fe1511e110fa52c7` (554,063 bytes). Production now stores and publishes ordinary complete `index.html` and `planner.html` files. Both files have the same digest. `/planner/` redirects to the root.

The one-time staging recovery workflow does not form part of production. No compressed fragment, reconstruction step, browser decompression loader or fallback to an older simplified planner remains in the Pages build.

## Tests and verification

Recovery run 34301540416 checked the release digest and parsed all 15 inline JavaScript blocks. HTTP-served Chromium smoke tests passed for `/` and `/planner.html`, including Pixel styling, canvas and template initialization, English/Chinese switching, opening/closing the architecture comparison dialog, and JSON download. These tests check loading and operation, not physical-model accuracy.

The production workflow checks integrity before publication and, after Pages deployment, requests both public URLs and compares the entire HTTP response digest to the frozen release. This post-deployment step must pass before a deployment is reported as verified.

No engineering model changes, manufacturing accuracy claims, license changes or arXiv submission are part of this repair.
