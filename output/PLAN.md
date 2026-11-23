# Project plan: status, study plan and agentic development

> Working document for the thesis on a LiteX-based SoC running Zephyr, with a Bus
> Firewall and OpenTitan security IPs. Written for the thesis author and their
> supervisor. Everything in §1 comes from the existing files in this folder
> (`README.md`, `docs/architettura_minima.md`, `docs/opentitan_panoramica.md`, and the
> log of the first Tang Primer build, now archived). Items not yet confirmed by a run keep
> the **[to be verified]** marker.

## 1. Summary of work done

- **LiteX 2026.08 installed**, with its ecosystem of cores (LiteDRAM, LiteEth, ...) and
  CPU packages.
- **First minimal build on the Sipeed Tang Primer 20K** (VexRiscv, ROM with BIOS, SRAM,
  UART). SoC generation and BIOS compilation succeeded (BIOS of 27.6 KiB). Synthesis
  stopped in the proprietary Gowin toolchain on a license verification error
  (`litex.log`).
- **Move to simulation** with `litex_sim` (Verilator): the same minimal system was built
  and booted to the BIOS prompt. This removes the dependency on the vendor toolchain and
  on flashing, and shortens the development loop.
- **Minimal architecture defined** in `architettura_minima/minimal_soc.py`: one parameter
  set applied to two targets, `sim` and `gatemate` (Olimex GateMate A1-EVB).

  | Item | Value |
  |---|---|
  | CPU | VexRiscv `standard` (RV32IM, I/D cache, 32 IRQ lines) |
  | Bus | Wishbone, 32-bit data and address |
  | ROM | 128 KiB @ `0x0000_0000` (BIOS) |
  | SRAM | 8 KiB @ `0x1000_0000` |
  | MAIN_RAM | 64 KiB @ `0x4000_0000` (Zephyr runs here) |
  | CSR region | 64 KiB @ `0xF000_0000` |
  | Peripherals | ctrl, identifier, timer0 (with uptime), uart (IRQ 0, 115200 baud) |
  | Clock | 1 MHz in simulation, 24 MHz (PLL) on the GateMate A1-EVB |

- **Zephyr overlay generation** (`overlay.dts`, `overlay.config`) from `csr.json` with
  the LiteX tool `litex_json2dts_zephyr`.
- **OpenTitan survey** (`docs/opentitan_panoramica.md`): security IPs, integration
  constraints in LiteX, and a proposed order: Wishbone→TL-UL adapter, `hmac`, `aes`
  without masking, entropy chain, `kmac`/`rom_ctrl`, then the key-manager group.
- **Thesis material**: draft of the architecture paragraph and a UML component diagram
  (`docs/component_diagram.svg`).

### Verification status

| Step | Status |
|---|---|
| Verilog, CSR map and overlay generation (`--no-compile`), both targets | Done |
| BIOS build for the new SoC | Done (23 Nov 2026) |
| Verilator simulation of the new SoC | Done: BIOS prompt reached, 64 KiB MAIN_RAM memtest OK (M0, 23 Nov 2026) |
| GateMate synthesis | Not run |
| Zephyr build with the generated overlay | Not run |

The environment was rebuilt on 23 Nov 2026 on macOS (Homebrew, Python 3.12 venv in
`~/.venvs/thesis`). GateMate synthesis and the Zephyr build are the next steps.

### Open items **[to be verified]**

- GateMate BRAM and logic budget (about 160 KiB of block RAM, about 20 000 logic
  elements).
- Whether 64 KiB of MAIN_RAM is enough for `hello_world`.
- Whether the GateMate flow (Yosys) accepts the OpenTitan SystemVerilog, or whether
  `sv2v` is needed.
- Zephyr driver coverage for the OpenTitan crypto IPs.
- Whether VexRiscv `secure` (PMP) works with the `litex_vexriscv` board, which declares
  the `standard` variant.

## 2. Study plan: Zephyr (scoped to project needs)

Each phase has a hands-on exercise in this repository and an exit criterion.

| Phase | Topics | Exit criterion |
|---|---|---|
| **Z0** Environment | Rebuild the venv; install RISC-V GCC, Zephyr SDK, `west`, Verilator | `minimal_soc.py --target sim --run` reaches the BIOS prompt |
| **Z1** Build system and board model | west, CMake, Kconfig, board/SoC split (HWMv2), the `litex_vexriscv` board files | `hello_world` built with the generated overlay and booted in simulation (`--ram-init`) |
| **Z2** Devicetree and bindings | DTS and overlays; `compatible` → binding YAML → driver; `DT_*` macros; the `litex,uart`, `litex,timer0`, `litex,soc-controller` bindings | Every node of the generated `overlay.dts` can be explained |
| **Z3** Drivers and interrupts | `DEVICE_DT_INST_DEFINE`, init levels, RISC-V IRQ path on LiteX, timer driver (`uptime_latch`) | Out-of-tree driver for a dummy CSR peripheral added to `minimal_soc.py` |
| **Z4** Custom board in a module | Out-of-tree Zephyr module, board definition for `sim` and `gatemate` | `west build -b litex_minimal/...` works for both targets |
| **Z5** Security-relevant subsystems | Crypto API (`crypto.h`), entropy API, PMP/userspace/MPU, Earl Grey board drivers as reference | A list mapping each planned IP to a Zephyr API |
| **Z6** Testing | Twister, ztest, tests on the Verilator target | One Twister test running on simulation |

## 3. Study plan: OpenTitan (scoped to project needs)

The order follows the IP integration order of `docs/opentitan_panoramica.md` §5.

| Phase | Topics | Exit criterion |
|---|---|---|
| **O1** Comportable IP and tooling | IP directory layout, Hjson register descriptions, `reggen` (RTL, C headers, docs), `prim` library | `hmac` register header generated out of tree |
| **O2** TL-UL protocol | A/D channels, integrity bits (`tlul_pkg`); design of the Wishbone→TL-UL adapter (or reuse of an existing bridge) | Verilator testbench showing read/write to a TL-UL register block |
| **O3** Standalone IP extraction | fusesoc core files, building `hmac` outside Earl Grey with Verilator, `sv2v`/Yosys for GateMate | `hmac` synthesised for GateMate, with LUT and BRAM numbers |
| **O4** Tie-off of system inputs | Alerts, `lc_ctrl` signals, EDN interface; what each tie-off gives up; `aes` with masking disabled | Documented tie-off table per IP |
| **O5** Software side | OpenTitan DIFs and their mapping to a Zephyr driver (crypto API shim) | Plan for an `hmac` driver |
| **O6** Later groups | Entropy chain, `kmac`/`rom_ctrl`, `keymgr`/`lc_ctrl`/`otp_ctrl`/`alert_handler`: read-only study; depth decided after O3 gives resource numbers | Updated IP roadmap |

**Bus Firewall.** OpenTitan has no direct equivalent. It is studied through LiteX
Wishbone internals (interconnect, arbiter, decoder) and compared with PMP: PMP limits
what software can address, the firewall filters the transactions of each master.

## 4. Milestones

| ID | Milestone | Date |
|---|---|---|
| M0 | Environment working, BIOS prompt in simulation | Sun 22 Nov |
| M1 | Zephyr `hello_world` booting in simulation | Tue 24 Nov |
| M2 | Same on the GateMate board (or synthesis report if the board is unavailable) | Fri 27 Nov |
| M3 | Zephyr board module `litex_minimal` | Mon 30 Nov |
| M4 | Wishbone→TL-UL adapter and `hmac` integrated in simulation | Mon 7 Dec |
| M5 | `hmac` driver in Zephyr, tested | Wed 9 Dec |
| M6 | Bus Firewall design | Thu 10 Dec |

## 5. Agentic development plan

AI coding agents (for example Claude Code) support the work as follows.

**Repository setup**
- `git init`, so every agent change can be reviewed and reverted.
- A `CLAUDE.md` with project context, the target memory map, build commands, and the
  rule "do not edit generated build directories by hand".
- Reproducible scripts (a Makefile or justfile) so agents and humans run the same
  commands.

**Roles and workflows**

| Role | What it does |
|---|---|
| Environment agent | Diagnoses toolchain problems (venv, SDK, Verilator) and writes a setup script |
| Build-and-run loop | Edits `minimal_soc.py` or Zephyr sources, runs the simulation headless (`--run`), reads the UART log, iterates. Simulation-first design makes this loop closed, with no hardware in it |
| Code-reading agent | Explores LiteX, Zephyr and OpenTitan sources (bindings, drivers, `tlul_pkg`, Hjson), answers study questions for each Z/O phase, writes notes into `docs/` |
| RTL helper | Drafts the Wishbone→TL-UL adapter, cocotb/Verilator testbenches and driver skeletons from Hjson. A human reviews all of it |
| Test agent | Writes Twister/ztest tests and maintains `make check` (generate → simulate → expect a UART string) |
| Documentation agent | Keeps the README and thesis drafts in sync with the code; translates between Italian and English |
| Review | `/code-review` on each change; parallel exploration subagents for large codebases |

**Guardrails**
- No item is marked as verified without real command output: the **[to be verified]**
  discipline continues.
- Security-critical RTL and tie-off decisions need human sign-off.
- Cite sources and versions (Zephyr and OpenTitan commits).
- Respect licensing when reusing OpenTitan code (Apache-2.0).
- Authorship stays clear: the agent drafts, the author decides.

**Measuring the benefit.** Track time per milestone and how often agent output needed
rework. This can become material for Chapter 6.

## 6. Thesis chapter structure (proposed)

| Ch. | Title | Source / state |
|---|---|---|
| 1 | Introduction (goal, contributions) | new |
| 2 | Background: 2.1 LiteX, 2.2 Zephyr, 2.3 OpenTitan | 2.3 from `opentitan_panoramica.md` |
| 3 | Minimal platform architecture | draft exists (`architettura_minima.md`) |
| 4 | Zephyr BSP for the LiteX platform | new |
| 5 | OpenTitan IP integration (Wishbone→TL-UL adapter and HMAC) | new |
| 6 | Agentic development methodology and assessment | new |
| 7 | Bus Firewall design and future work | new |
| 8 | Conclusions | new |

## 7. Daily schedule (Sat 21 Nov – Tue 15 Dec 2026)

Each day has three slots: **Study** (phase from §2/§3), **Hands-on** (agent-assisted
where it fits) and **Writing** (thesis chapter or section). Sundays are lighter buffer
and review days. A ★ marks a milestone.

| Date | Study | Hands-on | Writing |
|---|---|---|---|
| Sat 21 Nov | Z0: toolchain layout (RISC-V GCC, Zephyr SDK, Verilator) | `git init`, `CLAUDE.md`, rebuild `.venv`, install toolchains (environment agent) | Finalise this plan (§1 summary) |
| Sun 22 Nov | Z0: `litex_sim` internals | ★ M0: `minimal_soc.py --target sim --run` → BIOS prompt; `make check` skeleton | Ch3 §3: update verification status |
| Mon 23 Nov | Z1: west, CMake, Kconfig, HWMv2 board model | Build `hello_world` for `litex_vexriscv` with overlay | Ch2.2 Zephyr background (build system) |
| Tue 24 Nov | Z1: `litex_vexriscv` board/SoC files | ★ M1: boot Zephyr in sim via `--ram-init`; check 64 KiB MAIN_RAM | Ch4 §1 SoC→BSP build flow |
| Wed 25 Nov | Z2: devicetree, bindings, `DT_*` macros | Annotate every node of the generated `overlay.dts` | Ch4 §2 Devicetree and overlay |
| Thu 26 Nov | Z3: driver model, init levels, IRQ path, timer0 driver | Trace the uart and timer drivers in sim (code-reading agent) | Ch4 §3 Drivers and interrupts |
| Fri 27 Nov | GateMate flow (Yosys, place and route) | ★ M2: GateMate synthesis and resource report; board boot if available | Ch3: resolve BRAM/LUT **[to be verified]** items |
| Sat 28 Nov | Z3: out-of-tree drivers | Dummy CSR peripheral in `minimal_soc.py` and its Zephyr driver | Ch4 §4 Example custom driver |
| Sun 29 Nov | Buffer | Catch up on slipped items | Ch2.1 LiteX background; review of week 1 |
| Mon 30 Nov | Z4: Zephyr modules, custom boards | ★ M3: `litex_minimal` board (sim and gatemate) in a module | Ch4 §5 Custom board |
| Tue 1 Dec | Z6: Twister, ztest | Twister test on the sim target; wire into `make check` | Ch4 §6 Testing; start Ch6 notes (agent log) |
| Wed 2 Dec | O1: comportable IP, Hjson, `reggen`, `prim` | Generate `hmac` register RTL and header out of tree | Ch2.3 OpenTitan background (translate the survey) |
| Thu 3 Dec | O2: TL-UL protocol, `tlul_pkg`, integrity | Design the Wishbone→TL-UL adapter (agent drafts, human reviews) | Ch5 §1 Bus bridging problem |
| Fri 4 Dec | O2 (cont.) | Implement the adapter and a Verilator/cocotb testbench | Ch5 §2 Adapter design and verification |
| Sat 5 Dec | O3: fusesoc, `sv2v`, Yosys SystemVerilog support | Standalone `hmac` in Verilator; `sv2v`→Yosys for GateMate | Ch5 §3 IP extraction |
| Sun 6 Dec | Buffer | Catch up | Polish Ch2; review of week 2 |
| Mon 7 Dec | O4: tie-offs (alerts, lc, EDN) | ★ M4: integrate `hmac` in `minimal_soc.py` (sim); GateMate area numbers | Ch5 §4 Tie-off table and trade-offs |
| Tue 8 Dec | Z5 and O5: Zephyr crypto API, OpenTitan DIFs | `hmac` Zephyr driver (crypto API shim) | Ch5 §5 Software support |
| Wed 9 Dec | Z5 (cont.) | ★ M5: `hmac` test vectors via Twister in sim | Ch5 §6 Results |
| Thu 10 Dec | Bus Firewall: Wishbone internals, PMP, VexRiscv `secure` | ★ M6: prototype the firewall interface and CSR map (design only) | Ch7 §1 Bus Firewall design |
| Fri 11 Dec | O6: entropy chain, `kmac`/`rom_ctrl`, `keymgr` group (read-only) | None | Ch7 §2 Future work and IP roadmap |
| Sat 12 Dec | None | Collect agent metrics (time, rework rate) | Ch6 Agentic development; Ch1 Introduction |
| Sun 13 Dec | None | None | Ch8 Conclusions and abstract; full read-through |
| Mon 14 Dec | None | Agent-assisted consistency check (numbers vs. `csr.json` and logs) | Revision, figures, bibliography |
| Tue 15 Dec | None | None | Final proofreading; send to supervisor |

### Critical path and risks

- **Z0 (21–22 Nov) blocks everything.** If it slips, the Sunday buffers absorb it.
- **GateMate hardware may be unavailable on 27 Nov.** The board boot then moves to a
  buffer day; synthesis numbers alone are enough for Chapter 3.
- **Adapter and `hmac` work (4–9 Dec) carries the most risk.** If it slips, Chapter 5
  reports simulation-only results and the Zephyr driver becomes future work.

## 8. Immediate next steps

- [x] `git init` in the project folder and write the project rules (`.clinerules/project.md`).
- [x] Rebuild the environment (venv, Verilator, RISC-V GCC). Zephyr SDK and `west` still to do.
- [x] Run `minimal_soc.py --target sim --run` and reach the BIOS prompt (M0).
- [ ] Build Zephyr `hello_world` with `build/sim/overlay.dts` (M1).
