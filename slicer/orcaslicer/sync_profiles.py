#!/usr/bin/env python3
"""
Sync the Airwolf XL OrcaSlicer user presets between this repo and OrcaSlicer.

  python sync_profiles.py export   # OrcaSlicer -> repo (after changing presets in the GUI)
  python sync_profiles.py import   # repo -> OrcaSlicer (new PC / restore); close OrcaSlicer first

OrcaSlicer stays the source of truth; the repo keeps a reviewable snapshot.
Host keys (OctoPrint address and API key) never enter the repo: export blanks
them and import keeps whatever the local preset already has.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PRINTER_NAME = "Airwolf XL SchnerMod 0.4 nozzle"
PRESET_KINDS = ("machine", "filament", "process")
ORCA_USER_DIR = Path(os.path.expandvars(r"%APPDATA%\OrcaSlicer\user\default"))
REPO_DIR = Path(__file__).resolve().parent

# This repo is public: these stay on the local machine only.
LOCAL_ONLY_KEYS = ("print_host", "printhost_apikey", "printhost_user", "printhost_password", "printhost_cafile")


def load_preset(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_preset(path, preset):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(preset, f, indent=4, ensure_ascii=False)
        f.write("\n")


def belongs_to_airwolf(kind, preset):
    if kind == "machine":
        return preset.get("name") == PRINTER_NAME
    return PRINTER_NAME in preset.get("compatible_printers", [])


def is_orca_running():
    # tasklist prints in the OEM code page; only the ASCII image name matters here.
    tasks = subprocess.run(["tasklist", "/FI", "IMAGENAME eq orca-slicer.exe"],
                           capture_output=True, text=True, errors="replace")
    return "orca-slicer.exe" in tasks.stdout


def export_presets():
    if not ORCA_USER_DIR.is_dir():
        sys.exit(f"OrcaSlicer user presets not found at {ORCA_USER_DIR}")
    for kind in PRESET_KINDS:
        exported = set()
        for source in sorted((ORCA_USER_DIR / kind).glob("*.json")):
            preset = load_preset(source)
            if not belongs_to_airwolf(kind, preset):
                continue
            for key in LOCAL_ONLY_KEYS:
                if key in preset:
                    preset[key] = ""
            save_preset(REPO_DIR / kind / source.name, preset)
            exported.add(source.name)
            print(f"exported {kind}/{source.name}")
        # Deleting is a judgement call (renamed vs. retired preset), so only report it.
        for stale in sorted((REPO_DIR / kind).glob("*.json")):
            if stale.name not in exported:
                print(f"WARNING: {kind}/{stale.name} is in the repo but not in OrcaSlicer")


def import_presets():
    if is_orca_running():
        sys.exit("Close OrcaSlicer first: it keeps presets in memory and would overwrite the imported files.")
    for kind in PRESET_KINDS:
        for source in sorted((REPO_DIR / kind).glob("*.json")):
            preset = load_preset(source)
            target = ORCA_USER_DIR / kind / source.name
            if target.exists():
                local = load_preset(target)
                for key in LOCAL_ONLY_KEYS:
                    if local.get(key):
                        preset[key] = local[key]
            save_preset(target, preset)
            print(f"imported {kind}/{source.name}")


if __name__ == "__main__":
    actions = {"export": export_presets, "import": import_presets}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        sys.exit(__doc__)
    actions[sys.argv[1]]()
