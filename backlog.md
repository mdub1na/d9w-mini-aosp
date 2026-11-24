# D9W Mini firmware backlog

The next milestone is a repeatable AOSP 12 boot with the projector controls and a small set of TV apps. The same validated System can then cover a full acceptance run. During bring-up, keep the stock kernel, Vendor and partition layout. See the [bring-up evidence](docs/research/research-firmware-bringup.md) for the current baseline and its limits.

## Stages

| ID | Stage | Target |
| --- | --- | --- |
| `recovery` | Recovery | Verify R2 on the projector and retain a way to return to R1. |
| `daily-base` | Daily-use baseline | Repeat cold boot and sleep/wake, connect over an authenticated ADB session and qualify the thermal and shutdown path. |
| `core-apps` | Core apps | Build a reproducible System trial and validate WebView, Plume, UFM and VLC. |
| `hardware` | Projector hardware | Exercise optics, geometry, HDMI, audio and hardware decoding. |
| `connected` | Connected apps | Verify RuStore installation and upgrades, then video and sign-in in both TV streaming apps. |
| `release` | Joined acceptance | Run a complete device checklist on one candidate and rehearse the matching rollback. |

## Next decisions

- Prepare the reproducible System build and the core app manifest while testing the current boot. Keep the first on-device app trial small enough to isolate a startup regression.
- Use short hardware trials to establish basic function. Enable longer playback and combined validation after the thermal and shutdown gate passes.
- Keep APKs, OEM binaries, signing material, snapshots and raw logs in local storage. The public repository records provenance, contracts and reviewed results.

## Updating the queue

Each item in [`docs/backlog/`](docs/backlog/) has its own priority, stage, state and acceptance criteria. `blocked_by` records dependencies. Regenerate the index with `scripts/backlog_index.py` from the project’s docs-bootstrap skill after changing an item, then run the same script with `--check`.

`[ ]` open · `[~]` in progress · `[x]` done · `[?]` question · `[-]` dropped

<!-- BEGIN INDEX -->

## Open (12)

| Task | | Priority | Size | Blocked by |
|---|---|---|---|---|
| [B-01](docs/backlog/B-01-recovery-r2.md) `[~]` | Verify the Recovery R2 operation screen | P0 | S | - |
| [B-02](docs/backlog/B-02-remote-sleep-wake.md) `[ ]` | Make remote navigation and sleep/wake repeatable | P0 | M | - |
| [B-03](docs/backlog/B-03-authenticated-android-adb.md) `[ ]` | Verify Wi-Fi, Ethernet and authenticated Android ADB | P0 | M | - |
| [B-04](docs/backlog/B-04-reproducible-system-trial.md) `[ ]` | Reproduce the local System trial from pinned inputs | P0 | L | B-02 |
| [B-07](docs/backlog/B-07-qualify-projection-safety.md) `[ ]` | Qualify cold boot and projector safety with SELinux enforcing | P0 | L | B-04 |
| [B-05](docs/backlog/B-05-armv7-webview.md) `[ ]` | Restore a working ARMv7 WebView | P1 | M | B-04 |
| [B-06](docs/backlog/B-06-core-app-profile.md) `[ ]` | Integrate Plume, Ultimate File Manager and VLC | P1 | M | B-04 |
| [B-08](docs/backlog/B-08-restore-projector-optics.md) `[ ]` | Restore focus, geometry and the projector settings entry point | P1 | L | B-04 |
| [B-09](docs/backlog/B-09-qualify-av-paths.md) `[ ]` | Qualify HDMI input, audio and hardware video decoding | P1 | L | B-04 |
| [B-10](docs/backlog/B-10-qualify-rustore-tv.md) `[ ]` | Qualify RuStore TV installs and updates | P1 | M | B-03, B-04 |
| [B-11](docs/backlog/B-11-qualify-connected-tv-apps.md) `[ ]` | Qualify Kinopoisk TV and Rutube TV without Google services | P1 | M | B-03, B-05 |
| [B-12](docs/backlog/B-12-qualify-release-candidate.md) `[ ]` | Qualify the integrated release candidate and rehearse rollback | P1 | L | B-01, B-06, B-07, B-08, B-09, B-10, B-11 |

## Closed (0)

<!-- END INDEX -->
