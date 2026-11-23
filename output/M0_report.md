# M0 report

| Phase | Result | Key output |
|---|---|---|
| Phase 1 | pass | Backup created successfully with zip command and moved to project folder |
| Phase 2 | pass | All cleanup tasks completed successfully |
| Phase 3 | pass | Tools and libraries verified successfully || Phase 3 | pass | Homebrew 7.0.16, Python 3.12.16, Verilator 5.054, riscv64-elf-gcc 16.2.0 (rv32im/ilp32 libgcc present) |
| Phase 4 | pass | venv Python 3.12.16; litex/litex-boards editable from litex/; migen copied to site-packages; all litex/ repos clean |

| Phase 5 | pass | `BIOS CRC passed`, `CPU: VexRiscv @ 1MHz`, `MAIN RAM: 64.0KiB`, `Memtest OK`, `litex>` (first try failed: meson not on PATH because the venv was not activated; fixed with PATH, plan corrected) |
| Phase 6 | pass | git init, .gitignore, env.sh, .clinerules/project.md, .vscode/settings.json, README/PLAN updated; not committed |

## Notes
- Phase 2 deviations: backup zip was first left inside the project (moved to `~/LITEX-backup-20261123.zip` in Phase 6); `pythondata-cpu-cva6` reported a dirty nested submodule (symlinks turned into files) at the end of Phase 2, and was clean again after the Phase 4 install.
- Versions: Python 3.12.16, Verilator 5.054, riscv64-elf-gcc 16.2.0, Homebrew 7.0.16, LiteX 2026.08-213-gacbc4634e.
- Simulation log: `output/architettura_minima/build/sim/run.log` (BIOS prompt `litex>` at line 808).
- Memory map from `csr.json`: rom 0x0, sram 0x10000000, main_ram 0x40000000, csr 0xf0000000; ctrl 0xf0000000, identifier_mem 0xf0000800, timer0 0xf0001000, uart 0xf0001800.
