#!/usr/bin/env bash
# Boot the Zephyr image in the Verilator simulation. Usage: m1_run.sh [timeout_seconds]
set -uo pipefail
source /Users/davideriemma/Desktop/LITEX/env.sh
T="${1:-600}"
cd "$LITEX_ROOT/output/architettura_minima"
# The sleep keeps the simulator's stdin open; the log is also printed on screen.
sleep "$T" | gtimeout "$T" python minimal_soc.py --target sim --run \
  --ram-init "$HOME/zephyr-build/hello/zephyr/zephyr.bin" | tee build/sim/zephyr_run.log