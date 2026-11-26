# Project plan

> Thesis: **Sencha** (working name), a LiteX SoC for low-cost FPGAs with a VexRiscv host
> running Zephyr and a dedicated, active Root of Trust (Ibex + OpenTitan IPs) linked to
> the host only over SPI. Revised 26 Nov 2026. Earlier versions of this plan (with the
> detailed Zephyr/OpenTitan study plans) are in the git history; the M0 state is in tag
> `m0`. Items not confirmed by a run keep the **[to be verified]** marker.

## 1. Status

| Item | Status |
|---|---|
| Minimal SoC (`output/architettura_minima/minimal_soc.py`, targets `sim` and `gatemate`) | Done |
| M0: BIOS prompt in Verilator simulation, 64 KiB MAIN_RAM memtest | Done (23 Nov) |
| Security architecture, state of the art, novelty (`docs/rot_stato_arte_architettura.md`, `docs/component_diagram_rot.svg`) | Done (24 Nov) |
| Repository on GitHub (`davideriemma/sencha`), Apache-2.0 license, tag `m0` | Done (25 Nov) |
| Chapter 1 Introduction, bibliography, PDF (`output/thesis/`, not tracked) | Draft done (26 Nov) |
| M1: Zephyr `hello_world` in simulation | Not done (slipped from 24 Nov) |
| GateMate synthesis | Not run |

## 2. Architecture in one table

Details: `docs/rot_stato_arte_architettura.md` §4.

| Entity | Content |
|---|---|
| RoT | Ibex, TL-UL crossbar, boot ROM with signature check in software, `sram_ctrl`, `hmac`, emulated `otp_ctrl`, reduced `lc_ctrl`, `spi_host` (sole master of the boot flash), `spi_device`, gpio/rstmgr, timers. Later: entropy chain, `alert_handler`, `keymgr`/`aes`. Excluded for area: `otbn`, `kmac` |
| Host | VexRiscv, ROM boot stub, SRAM, MAIN_RAM, UART, timer, GPIO, watchdog, SPI master for ADCs/memories, networking (LiteEth, or W5500/ENC28J60 on SPI), Bus Firewall (planned) |
| Link | SPI to `spi_device` with two chip selects (mailbox, filtered flash passthrough), plus `HOST_RST_N` and `ROT_IRQ` |
| Software | MCUboot, generated Zephyr board, opaque PSA Crypto driver over the mailbox |

## 3. Thesis chapters

| Ch. | Title | Depends on | First draft |
|---|---|---|---|
| 1 | Introduction | — | Done 26 Nov |
| 2 | Background: LiteX, Zephyr, OpenTitan, Roots of Trust | existing docs | Thu 26 Nov |
| 3 | Platform Architecture: Host SoC, Dedicated RoT and Inter-Chip Link | existing docs | Fri 27 Nov |
| 4 | Zephyr BSP for the LiteX Platform | M1 | Tue 1 Dec |
| 5 | Dedicated RoT: Mini TL-UL Top, Tie-offs, Boot ROM and Secure Boot | M2 (design), M4/M5 (results) | Thu 3 Dec |
| 6 | Agentic Development Methodology and Assessment | session logs | Sat 28 Nov |
| 7 | Link Protocol, PSA Driver, Bus Firewall and Future Work | design only | Sun 29 Nov |
| 8 | Conclusions | all results | Fri 4 Dec (draft), Thu 10 Dec (final) |

Chapters that depend on results are drafted with placeholders and completed on 10 Dec.

## 4. Milestones

| ID | Milestone | Date |
|---|---|---|
| M1 | Zephyr `hello_world` booting in simulation | Mon 30 Nov |
| M2 | GateMate synthesis: resources of the host alone and of Ibex alone | Wed 2 Dec |
| M4 | Mini RoT top next to the host in simulation, SPI link and `HOST_RST_N` wired | Mon 7 Dec |
| M5 | Secure boot in simulation: signed image boots, altered or rolled-back image keeps the host in reset | Wed 9 Dec |

## 5. Daily schedule (Thu 26 Nov – Wed 16 Dec 2026)

Weekends are spent at home: writing only, no board or lab work.

| Date | Activity | Output |
|---|---|---|
| Thu 26 Nov | Ch2 Background | Ch2 draft |
| Fri 27 Nov | Ch3 Architecture | Ch3 draft |
| Sat 28 Nov (home) | Ch6 Agentic methodology | Ch6 draft |
| Sun 29 Nov (home) | Ch7 Link protocol, PSA driver, Bus Firewall (design) | Ch7 draft |
| Mon 30 Nov | M1: Zephyr `hello_world` in simulation | M1 |
| Tue 1 Dec | Ch4 Zephyr BSP, with M1 results | Ch4 draft |
| Wed 2 Dec | M2: GateMate synthesis (host, Ibex) | Resource report |
| Thu 3 Dec | Ch5 Dedicated RoT (design, placeholders for results) | Ch5 draft |
| Fri 4 Dec | Ch8 Conclusions (draft) and abstract | All chapters drafted |
| Sat 5 – Sun 6 Dec (home) | Buffer: catch up on slipped items, light rereading | — |
| Mon 7 – Wed 9 Dec | M4 and M5: mini RoT top and secure boot in simulation | Results for Ch5 |
| Thu 10 Dec | Complete Ch4, Ch5 and Ch8 with results | Chapters complete |
| Fri 11 Dec | Review Ch1–3; single bibliography | — |
| Sat 12 – Sun 13 Dec (home) | Review Ch4–8; figures; numbers checked against logs | — |
| Mon 14 Dec | Full review; single thesis PDF | Complete draft |
| Tue 15 Dec | Final corrections | — |
| Wed 16 Dec | Send to the supervisor | Thesis sent |

## 6. Working method

- **Claude Opus-class agents**: reasoning, architecture, research coordination, review of
  everything produced. Web research is delegated to Sonnet subagents.
- **Local agents (Qwen on LM Studio)**: code and file edits, commits, text drafts from a
  precise outline. Every run is approved by the author beforehand and checked afterwards
  against an expected result and the run log.
- **Chapters**: outline → sources (Sonnet) → draft (Qwen) → fact and citation check
  (Opus) → author review → PDF from Markdown.
- **Rules**: nothing is marked done without command output; no bibliography author is
  added unless verified (gaps go to `output/thesis/missing_authors.md`); OpenTitan code
  is reused under Apache-2.0.

## 7. Risks

- **M1 already slipped.** If it slips again, Ch4 moves to the 5–6 Dec buffer.
- **M4/M5 (7–9 Dec) carry the most risk.** If they slip, Ch5 reports the design and
  partial simulation results; signature checking stays in the host-side MCUboot and the
  PSA driver becomes future work.
- **GateMate area.** Two CPUs plus the RoT IPs may not fit. Fallbacks: drop networking
  from the board build, put RoT and host on separate boards, or report synthesis on a
  larger FPGA.
- **Local model stability.** The 30B model crashed twice on 26 Nov; the 9B model is the
  fallback (slower, it reasons before answering).

## 8. Open items **[to be verified]**

- GateMate logic and BRAM budget for two CPUs and the phase-1 RoT IPs.
- Whether 64 KiB of MAIN_RAM is enough for `hello_world`.
- Whether the GateMate flow (Yosys) accepts the OpenTitan SystemVerilog, or `sv2v` is needed.
- Whether `top_englishbreakfast` and `tlgen` can be the base of the mini RoT top.
- GateMate bitstream encryption; Ethernet PHY on the A1-EVB.
- Opaque PSA driver for an external secure element in Zephyr upstream.
- Code size and boot time of signature verification in software on Ibex.
