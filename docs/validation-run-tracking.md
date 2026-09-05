# Physical validation run tracking

The primary full pilot is GitHub Actions run 33963302104 at benchmark commit 194ab85fd1f6058b772fe9a7daa4d1fe882068b2. It runs 18 RTL configurations and two routing budgets per configuration. This document is not a claim that the run has finished or that all cases succeeded.

The successful earlier run 33963042647 is a three-configuration smoke test only. Its artifact (9968547836) verifies the synthesis/placement/global-routing plumbing and resource-baseline extraction, not held-out accuracy.

Important scope: post-placement pin-coordinate adapter; one public Nangate45 typical library; projected H/V signal-routing pressure; threshold >= 0.8 for hotspots. No signoff, full no-RTL validation, or cross-foundry accuracy claim is made.
