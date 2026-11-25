# Sencha: LiteX SoC with Zephyr and a dedicated OpenTitan-based RoT

Sencha is a working name for this project, which implements a LiteX-based System-on-Chip (SoC) running Zephyr RTOS, with a dedicated Root of Trust (RoT) built from OpenTitan IP cores.

## Project Overview

The project implements a minimal LiteX SoC architecture that can be instantiated for both Verilator simulation and Olimex GateMate A1-EVB FPGA targets. The architecture features:

- **VexRiscv CPU** (RV32IM) as the main host processor
- **Wishbone bus** connecting components
- **Memory map**: 
  - 128 KiB ROM (BIOS)
  - 8 KiB SRAM
  - 64 KiB MAIN_RAM (Zephyr execution space)
  - 64 KiB CSR region

## Key Features

1. **Dual Target Architecture**: The same SoC definition works for both simulation (`sim`) and actual FPGA hardware (`gatemate`)
2. **Zephyr Integration**: Generates device tree overlays and Kconfig files for seamless Zephyr BSP integration
3. **Security Architecture**: A dedicated RoT (Root of Trust) with OpenTitan IPs (Ibex CPU, HMAC, SPI interfaces) (designed, not implemented)
4. **Secure Boot**: RoT verifies signed host images before releasing reset (planned, designed)
5. **PSA Crypto Integration**: Host software will integrate with PSA Crypto APIs (planned, designed)
6. **Targets low-cost FPGAs** (GateMate A1-EVB)

## Components

- `output/architettura_minima/minimal_soc.py`: Main SoC definition with dual targets (sim/gatemate)
- `output/docs/rot_stato_arte_architettura.md`: Detailed security architecture and RoT design
- `output/docs/architettura_minima.md`: Documentation of minimal SoC architecture  
- `output/docs/opentitan_panoramica.md`: Overview of OpenTitan IPs used
- `output/docs/component_diagram_rot.svg`: Component diagram for RoT architecture
- `output/PLAN.md`: Project plan and roadmap

## Status

| Milestone | Description | Status |
|----------|-------------|--------|
| M0 (BIOS prompt in Verilator simulation) | BIOS boots and shows prompt | Done, 23 Nov 2026 |
| M1 (Zephyr hello_world in simulation) | Zephyr builds and runs on SoC | In progress |
| GateMate synthesis | FPGA bitstream generation | Not run |
| RoT, secure boot, PSA driver | Hardware and software integration | Designed, not implemented |

## Architecture Summary

**Host**: VexRiscv (RV32IM) + Wishbone + LiteX cores (UART, timer, SPI master for ADCs/memories, networking planned)  
**RoT**: Ibex + TL-UL crossbar + OpenTitan IPs (hmac, spi_device, spi_host, emulated OTP, reduced lc_ctrl)  
**Link**: SPI with two chip selects (mailbox, filtered flash passthrough) plus HOST_RST_N and ROT_IRQ lines  

## Requirements

- LiteX (cloned into ./litex, not tracked)
- Python venv
- Verilator
- RISC-V GCC
- Zephyr SDK and west  
- `env.sh` to set up the environment (it contains absolute paths of the author's machine: adapt them)

## Usage

```bash
cd output/architettura_minima
./minimal_soc.py --target sim --run

# Build Zephyr with generated overlay  
west build -b litex_vexriscv samples/hello_world -DDTC_OVERLAY_FILE=<...>/build/sim/overlay.dts
```

## Thesis Focus

This project aims to show how to build a cost-effective, open-source secure IoT platform that:
- Integrates Zephyr RTOS with hardware security
- Uses a dedicated RoT for secure boot functionality (planned)
- Provides transparent software integration through PSA Crypto APIs (planned)  
- Quantifies security costs on low-cost FPGA platforms (planned)

The work addresses the gap between proprietary secure solutions and open, minimal-security implementations for IoT applications.

## License

Copyright 2026 davideriemma

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text.

Third-party components are not part of this repository and keep their own licenses: LiteX (cloned into `./litex`, BSD-2-Clause) and the OpenTitan IP cores planned for the RoT (Apache-2.0, compatible with this license).
