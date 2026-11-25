#!/usr/bin/env bash
# Build Zephyr hello_world for the minimal SoC (sim) with the generated overlay.
set -euo pipefail
source /Users/davideriemma/Desktop/LITEX/env.sh
cd "$ZEPHYR_BASE"
west build -p always -b litex_vexriscv samples/hello_world \
  -d "$HOME/zephyr-build/hello" -- \
  -DDTC_OVERLAY_FILE="$LITEX_ROOT/output/architettura_minima/build/sim/overlay.dts"