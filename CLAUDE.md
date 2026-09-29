# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **fork of Marlin 2.1.x firmware** (branch `bugfix-2.1.x`) configured for a specific
machine: an **Airwolf XL** printer driven by a **BigTreeTech SKR Mini E3 V3.0** board
(MCU: STM32G0B1RET6, ARM Cortex-M0+). Upstream is `MarlinFirmware/Marlin`; the local
remote is `schner/Marlin-Airwolf3D-XL-BTT-Mini-E3-V3`.

The C++ firmware source under `Marlin/src/` is upstream Marlin and is rarely touched.
**The actual product of this repo is the machine configuration** — three files carry
all the customization and are normally the only ones with uncommitted changes:

- `Marlin/Configuration.h` — core machine config
- `Marlin/Configuration_adv.h` — advanced/tuning config
- `ini/features.ini` — maps feature flags to library deps + source filters

When asked to "change the printer", "fix homing", "adjust the probe", etc., edit those
files — not the firmware modules.

Slicer presets (OrcaSlicer) are versioned separately in `slicer/orcaslicer/`. OrcaSlicer
(`%APPDATA%\OrcaSlicer\user\default`) is the source of truth; `sync_profiles.py export`
refreshes the repo snapshot and blanks the OctoPrint host/API key (the repo is public).
Never commit `printhost_apikey`.

## Build, flash, test

PlatformIO is the build system. Default environment is `STM32G0B1RE_btt` (set in
`platformio.ini`). Build via the **Auto Build Marlin** VSCode extension (recommended) or:

```bash
platformio run -e STM32G0B1RE_btt        # build the configured board
make marlin                               # build via buildroot/bin/mftest -a
```

**Flashing is not over USB.** This board uses a bootloader (firmware offset `0x2000`).
The build produces `.pio/build/STM32G0B1RE_btt/firmware.bin`; copy it to the **root of
the SD card**, insert it, and power-cycle the printer. The bootloader flashes and
renames the file.

### Tests

Marlin has two distinct test systems, both driven by the top-level `Makefile`:

1. **Config build tests** — compile the firmware against example configs to catch
   `#if`/macro breakage. Requires `pyyaml` (`python -m pip install pyyaml`).
   ```bash
   make tests-single-local TEST_TARGET=STM32G0B1RE_btt   # build test for this board
   make tests-all-local                                  # all CI build tests
   make tests-single-local-docker TEST_TARGET=...        # same, in Docker
   ```
   Test scripts live in `buildroot/tests/<TEST_TARGET>`. `ONLY_TEST=<name|index>`
   narrows to one sub-test. `GIT_RESET_HARD=true` (used by CI) **discards local
   changes** — never run it with unsaved config edits.

2. **Unit tests** — compiled and run natively (no hardware) via the `linux_native_test`
   env. Test files live in `Marlin/tests/`.
   ```bash
   make unit-test-all-local                              # all unit suites
   make unit-test-single-local UNIT_TEST_CONFIG=<name>   # one config's suites
   platformio run -t marlin_<suite> -e linux_native_test # one suite via PIO
   ```

Other Makefile helpers: `make format-pins -j`, `make validate-pins -j`,
`make validate-boards`.

## Architecture (big picture)

Marlin targets dozens of boards through a **Hardware Abstraction Layer**. The pieces that
matter when navigating the source:

- `Marlin/src/HAL/<platform>/` — per-MCU implementations behind a common API. This board
  uses `HAL/STM32/`. Platform selection flows from `MOTHERBOARD` → pins file → HAL.
- `Marlin/src/pins/` — board pin maps. `src/core/boards.h` lists every `BOARD_*` id; the
  matching pins header wires that id to physical MCU pins. This board:
  `BOARD_BTT_SKR_MINI_E3_V3_0`.
- `Marlin/src/module/` — motion core: `planner`, `stepper`, `motion`, `temperature`,
  `endstops`, `probe`, `settings` (EEPROM/M500). This is the real-time heart.
- `Marlin/src/gcode/` — one folder per G-code category; each command in its own file
  (e.g. `gcode/calibrate/G28.cpp`). New G-codes are added here.
- `Marlin/src/feature/` — optional features (BLTouch, filament runout, LEDs, MMU, …),
  each gated by a `Configuration*.h` flag and a `build_src_filter` entry.
- `Marlin/src/inc/` — `Conditionals_*.h` and `SanityCheck.h` derive dependent settings
  and **fail the build with `#error` on invalid config combos**. Most config mistakes
  surface here, not at runtime.
- `Marlin/src/lcd/` — display/UI drivers.

**Config → build coupling:** PlatformIO runs `buildroot/share/PlatformIO/scripts/`
(notably `configuration.py` and `common-dependencies.py`) as pre-build steps. They read
the enabled `#define`s and pull the matching `lib_deps` / source files from `ini/*.ini`.
So enabling a feature usually means a `Configuration*.h` flag **and** a corresponding
`ini/features.ini` entry — flipping the define alone may not link the code in.

`platformio.ini`'s `[common] default_src_filter` aggressively excludes source by default
and re-includes a minimal set; the per-feature filters add the rest back. Don't be
surprised that most of `src/` is excluded until a feature turns it on.

## The physical machine

This firmware drives a heavily-modified **Airwolf 3D XL** (cartesian), not a stock
printer. Knowing the mechanics explains the config choices:

- **Extruder:** Bulldog XL, **direct drive** → short retractions (0.8–1.0 mm), never the
  long Bowden-style values.
- **Hotend:** BP6 (copper block, all-metal or PTFE-lined throat options), 1.75 mm,
  **0.4 mm** nozzle, silicone sock now installed. Nozzle options on hand: PTFE-plated
  brass (best flow, PLA/PETG), hardened steel (abrasives/GF), titanium alloy.
  After any hotend hardware swap (sock/nozzle/block/throat): re-run MPC autotune
  (`M306 T` + `M500`) and re-set Z-offset/mesh.
- **Probe:** BLTouch. **Bed:** heated, dual-sided magnetic plate (textured/smooth).
- **Host:** Raspberry Pi 4 running OctoPrint + OctoDash; Logitech C920 for timelapse
  (Octolapse). Onboard touch screen present.
- **Serial:** `SERIAL_PORT 2`, `BAUDRATE 115200`, `SERIAL_PORT_2 -1`. ⚠️ The host/PIO
  serial monitor must use **115200** — `platformio.ini`'s `monitor_speed = 250000` does
  **not** match the firmware.

Full machine context (calibration state, mesh, Cura profiles, Octolapse, diagnostic
routines, safety rules) lives in [docs/AIRWOLF-SchnerMod.md](docs/AIRWOLF-SchnerMod.md).
Read it before tuning anything print-quality related.

## ⚠️ Compiled defaults vs. live EEPROM — read before editing config

`EEPROM_SETTINGS` is enabled. The running printer's values come from **EEPROM** (set via
G-code + `M500`), not from `Configuration*.h`. So:

- **Editing `Configuration.h` does NOT change a running machine** until an `M502`
  (reset to compiled defaults) or a flash with reset EEPROM. Routine config edits +
  reflash leave the saved EEPROM values in place.
- Conversely, several live values were tuned in G-code and **diverge from the source**.
  Confirmed divergences (verify current state with `M503` before acting):

  | Param | Compiled (`Configuration*.h`) | Live EEPROM (`M503`) |
  |---|---|---|
  | Hotend PID | 12.54 / 0.88 / 44.63 | 12.92 / 0.84 / 49.60 |
  | Bed PID | 50.57 / 7.35 / 231.93 | 95.54 / 18.66 / 326.11 |
  | Probe Z offset | −3.88 | −2.93 (`M851`) |
  | Print / travel accel | 3000 / 5000 | 1200 / 1200 (`M204`) |
  | Filament runout | enabled | off (`M412 S0`) |

- To make a tuned value survive `M502`, mirror it into `Configuration*.h` **and** keep
  the EEPROM copy. The machine is still in fine calibration — treat retraction, Linear
  Advance (currently `M900 K0`), speeds, flow, and PID as not-yet-final.

**Safety (never override to "fix" a symptom):** don't disable/loosen `THERMAL_PROTECTION`;
don't run `M502` without an `M503` backup first; don't raise driver current, max temp,
acceleration, or extruder feedrate without validating the hardware physically.

## This machine's notable config (vs. stock Ender-3 SKR Mini E3)

Deliberate deviations in `Configuration*.h` — preserve them; don't "fix" them to defaults:

- `CUSTOM_MACHINE_NAME "Airwolf-XL-V4.7.6"`, author tag `M Schner IT`
- Bed **275 × 200**, `Z_MAX_POS 160`, `X_MIN_POS -16`
- ⚠️ **`M206 X-16` (home offset) is REQUIRED and lives only in EEPROM.** The machine's X
  endstop sits ~16 mm further left than `X_MIN_POS` alone accounts for; without the M206
  offset, `G29` drives the probe past the physical X end and **crashes into the frame**.
  It survives a normal reflash but **`M502` wipes it** — after any `M502`, re-apply
  `M206 X-16` + `M500` BEFORE homing/G29. (Not yet baked into `Configuration.h`; doing so
  needs verifying the real endstop-to-bed geometry, not guessing X_MIN/X_MAX.)
- **BLTouch** with `AUTO_BED_LEVELING_BILINEAR` (5×5 grid, fade height 10 mm),
  `Z_SAFE_HOMING`, `USE_PROBE_FOR_Z_HOMING`; `NOZZLE_TO_PROBE_OFFSET { 38, 0, -3.88 }`
- TMC2209 on X/Y/Z/E0; X/Y/Z RMS current raised to **1200 mA** (E0 at 800 mA)
- `FILAMENT_RUNOUT_SENSOR` + `FILAMENT_MOTION_SENSOR` compiled in (disabled in EEPROM)
- NeoPixel strip: 32 LEDs on `PA8`
- Bed thermistor `TEMP_SENSOR_BED 13`, retuned hotend PID
- Steps/unit `{ 66.6666, 66.6666, 2560, 454.13 }`; **E feedrate capped at 25 mm/s**
  (`DEFAULT_MAX_FEEDRATE` E) — this is why retract/prime speeds above 25 are pointless
- `LIN_ADVANCE`, `ARC_SUPPORT`, `AUTOTEMP` compiled in (Linear Advance K0 at runtime;
  don't enable AUTOTEMP by accident)
- `INVERT_E0_DIR true`
- Debug flags currently on (`DEBUG_LEVELING_FEATURE`, `PINS_DEBUGGING`) — tuning aids;
  consider disabling for a production/release build.
- **Silicone sock now installed** (was missing) → thermal margin improved, the
  earlier fan-induced temp sag should ease. Still never loosen `THERMAL_PROTECTION`.
  Re-run MPC autotune (`M306 T`) with the sock on. `HOTEND_IDLE_TIMEOUT` stays enabled
  as general heat-creep safety.

## Advanced features (round of 2026-06-25)

The fork already shipped: runout + `FILAMENT_MOTION_SENSOR`, `NOZZLE_PARK_FEATURE`,
`ADVANCED_PAUSE_FEATURE` + `PARK_HEAD_ON_PAUSE` + M701/M702, `HOST_ACTION_COMMANDS` +
`HOST_PROMPT_SUPPORT` (OctoPrint), `LIN_ADVANCE`, `ARC_SUPPORT`, `ADAPTIVE_STEP_SMOOTHING`,
`BABYSTEPPING`, `EMERGENCY_PARSER`, `SET_PROGRESS_MANUALLY`.

Added this round (`Configuration_adv.h` unless noted), each needing calibration where flagged:

- **`FT_MOTION`** (Fixed-Time Motion) — replaces Input Shaping (the two are mutually
  exclusive; `INPUT_SHAPING_*` and `S_CURVE_ACCELERATION` are off). ZV shaper on X/Y,
  default 37 Hz, `FTM_IS_DEFAULT_MOTION` on, `FT_MOTION_MENU` for on-LCD tuning.
  **Must calibrate** shaper frequency per axis (ringing tower → `M493`). K factor is set
  with `M900 K` (shared with `LIN_ADVANCE`). ⚠️ FT_MOTION is BETA and CPU-heavy; the
  STM32G0 (M0+ @ 64 MHz, no FPU) may not keep up at high speed — verify on the machine,
  fall back to Input Shaping if it stutters.
- **`MPCTEMP`** (Model Predictive Control) — replaces hotend `PIDTEMP` (now off; bed still
  uses PID). `MPC_AUTOTUNE` + edit/autotune LCD menus on. **Must run `M306 T` then `M500`**
  before printing or temps are uncontrolled. Better at fan-induced temp drops (the no-sock
  symptom). Hotend PID values kept commented for revert.
- `HYBRID_THRESHOLD` — StealthChop below / SpreadCycle above per-axis thresholds
  (XY 100 mm/s) for torque at speed.
- `HOTEND_IDLE_TIMEOUT` — cools the nozzle after 5 min idle >180 °C (no-sock safety).
- `MONITOR_DRIVER_STATUS` (+ `STOP_ON_ERROR`, `CURRENT_STEP_DOWN 50`) — TMC over-temp watch.
- `BABYSTEP_ZPROBE_OFFSET` — live babystep writes back to the M851 Z offset (PEI first layer).
- `G29_RETRY_AND_RECOVER` (3 retries) — BLTouch probe-fail recovery.
- `SET_REMAINING_TIME` + `SHOW_REMAINING_TIME` — ETA on display, fed by host `M73 R`.
- `CANCEL_OBJECTS` — `M486` object cancel (OctoPrint).
- `BOARD_HAS_DCDC5V` + `NEOPIXEL_PIXELS 29` (Configuration.h) — satisfies the upstream
  NeoPixel current guard; strip is externally powered by a DC-DC buck (physical strip 32,
  last 3 unused).

Calibration procedures: see [docs/CALIBRATION.md](docs/CALIBRATION.md).

**Verified:** `platformio run -e STM32G0B1RE_btt` succeeds — Flash 56.3% (290 KB/504 KB),
RAM 15.4% (23 KB/144 KB).

**Not enabled — `POWER_LOSS_RECOVERY`:** pin conflict. `FIL_MOTION1_PIN` is mapped to
`POWER_LOSS_PIN`, so the motion sensor and PLR can't coexist on the stock wiring.

**Upstream:** synced to `marlin/bugfix-2.1.x` @ 2026-06-25 (merge `6f54964b7f`). The pre-sync
state is preserved on branch `pre-upstream-merge-2026-06-25` as a restore point. Future
syncs: `git fetch marlin && git merge marlin/bugfix-2.1.x` — conflicts land only in the two
config files; resolve by keeping machine values and adopting upstream's new option structure
(watch for renamed macros, e.g. the PID `DEFAULT_Kp`→`DEFAULT_KP` rename in this sync).

## Contributing conventions (upstream)

- Patches target the `bugfix-2.1.x` branch.
- New features should add a build test under `buildroot/tests/` and, when unit-testable,
  a suite under `Marlin/tests/`.
- Pins files must pass `make validate-pins`; `boards.h` must pass `make validate-boards`.
- Follow Marlin coding standards (https://marlinfw.org/docs/development/coding_standards.html).
