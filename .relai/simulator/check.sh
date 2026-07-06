#!/usr/bin/env bash
set -euo pipefail

# RELAI managed requirements:
# - validate the simulator-local venv, not ROOT_DIR/.venv
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SIM_DIR="$ROOT_DIR/.relai/simulator"
VENV_DIR="$SIM_DIR/.venv"

relai_simulator_python_path() {
  local venv_dir="$1"
  if [ -x "$venv_dir/bin/python" ]; then
    printf '%s\n' "$venv_dir/bin/python"
  elif [ -x "$venv_dir/Scripts/python.exe" ]; then
    printf '%s\n' "$venv_dir/Scripts/python.exe"
  else
    printf '%s\n' "$venv_dir/bin/python"
  fi
}

VENV_PYTHON="$(relai_simulator_python_path "$VENV_DIR")"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Simulator virtualenv is missing. Run .relai/simulator/install.sh" >&2
  exit 1
fi

PYTHONPATH="$SIM_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
"$VENV_PYTHON" - "$VENV_DIR" "$SIM_DIR/smoke_learning_env.py" <<'PY'
import importlib
from pathlib import Path
import sys

import relai

venv_dir = Path(sys.argv[1]).resolve()
smoke_env_path = Path(sys.argv[2]).resolve()
# Keep the launched interpreter path as-is so framework/symlinked Python builds
# still validate against the simulator-local venv path.
executable = Path(sys.executable)
if not executable.is_absolute():
    executable = executable.absolute()
prefix = Path(sys.prefix).resolve()


def venv_root_for_python(path: Path) -> Path:
    return path.parent.parent.resolve()


actual_executable_venv_dir = venv_root_for_python(executable)

if actual_executable_venv_dir != venv_dir:
    raise SystemExit(
        "Simulator Python must come from the simulator venv.\n"
        f"Expected venv dir: {venv_dir}\n"
        f"Actual executable: {sys.executable!r}\n"
        f"Actual executable venv dir: {actual_executable_venv_dir}"
    )

if prefix != venv_dir:
    raise SystemExit(
        "Simulator sys.prefix must point at the simulator venv.\n"
        f"Expected venv dir: {venv_dir}\n"
        f"Actual sys.prefix: {sys.prefix!r}"
    )

for module_name in ["relai", "relai_simulator", "airline_support.agent"]:
    importlib.import_module(module_name)

environment = relai.load_learning_environment(smoke_env_path)
if environment.id != "relai-init-smoke":
    raise SystemExit(
        "Unexpected smoke learning environment id.\n"
        f"Expected: 'relai-init-smoke'\n"
        f"Actual: {environment.id!r}"
    )
PY
