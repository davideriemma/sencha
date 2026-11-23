# Project rules

Thesis project: a LiteX SoC (VexRiscv, Wishbone) running Zephyr, in Verilator simulation first,
then on the Olimex GateMate A1-EVB. Later: Bus Firewall and OpenTitan IPs. See output/PLAN.md.

## Layout
- Sources: /Users/davideriemma/Desktop/LITEX/litex/ (git clones, never edit)
- SoC script: output/architettura_minima/minimal_soc.py (targets sim, gatemate)
- Generated files: output/architettura_minima/build/ (never edit by hand, regenerate)
- Python venv: /Users/davideriemma/.venvs/thesis. Use `source env.sh`.

## Memory map
| Region | Base | Size |
|---|---|---|
| ROM | 0x0000_0000 | 128 KiB (BIOS) |
| SRAM | 0x1000_0000 | 8 KiB |
| MAIN_RAM | 0x4000_0000 | 64 KiB |
| CSR | 0xF000_0000 | 64 KiB |

## Commands (after `source env.sh`; the venv bin/ must be on PATH so LiteX finds meson and ninja)
- Generate only: `cd output/architettura_minima && ./minimal_soc.py --target sim --no-compile`
- Simulate:      `cd output/architettura_minima && ./minimal_soc.py --target sim --run`
  (needs a stdin that stays open; the first build takes about 2 minutes)

## Rules
- Do not edit litex/ or minimal_soc.py unless the user asks.
- Never mark something as verified without real command output. Keep the "[to be verified]" marker.
- No sudo, no git commit, no installs without asking.
- Security-critical RTL and tie-off decisions need human sign-off.

## Installed versions (23/11/2026)
| Tool | Version |
|---|---|
| Python (venv) | 3.12.16 |
| Verilator | 5.054 |
| riscv64-elf-gcc | 16.2.0 (Homebrew; rv32im/ilp32 libgcc present) |
| LiteX | 2026.08-213-gacbc4634e |
