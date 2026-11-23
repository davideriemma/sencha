# human-plan.md — Clean start and milestone M0 (macOS)

## Context

The project moved back to this Mac (macOS, Apple Silicon, 24 GB RAM). Nothing from the old
Linux VMs works here:
- `.venv/` points to `/usr/bin/python3.12` of a Linux machine.
- `.vscode/settings.json` points to `/home/davide/...`.
- There is no Homebrew, Verilator or RISC-V compiler. The system Python is 3.9.

The LiteX sources in `litex/` (2.6 GB, LiteX `2026.08-213`) are fine and are kept.

**Goal: M0** = the LiteX BIOS prompt (`litex>`) in a Verilator simulation of the minimal SoC.
Zephyr (M1) and the GateMate board come after M0.

The work is done by qwen3-coder-30b in Cline, following [agent-plan.md](agent-plan.md). You do
what needs a password or a decision.

## Clean starting condition

```
LITEX/
├── agent-plan.md   human-plan.md   inst.txt
├── .gitignore      .clinerules/project.md   env.sh      (created by the agent, Phase 6)
├── .vscode/settings.json                                 (rewritten)
├── litex/                      git clones, caches removed, not tracked by git
└── output/
    ├── README.md   PLAN.md   M0_report.md                 (README/PLAN updated)
    ├── docs/       architettura_minima.md, opentitan_panoramica.md, component_diagram.*
    └── architettura_minima/minimal_soc.py                 (build/ regenerated, not tracked)
```

Outside the project: `~/.venvs/thesis` (Python 3.12) and `~/LITEX-backup-20261123.zip`.

**What gets deleted** (Phase 2): `.venv/`, the old Tang Primer build (`output/gateware`,
`output/software`, `output/csr.*`, `output/litex.log`), `output/architettura_minima/build/`,
`output/thesis_schedule.ics`, and the Python caches inside `litex/`. The backup zip is made
**before** anything is deleted and holds everything except `litex/` and `.venv/`.

## Steps for you

### 1. Before starting
- If you have not yet imported `output/thesis_schedule.ics` into your calendar, do it now:
  it is deleted in Phase 2 (it can be regenerated from `PLAN.md` §7 if needed).
- Close or save any open editors with files from `output/`.

### 2. Install the tools (needs your password)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
brew install python@3.12 verilator riscv64-elf-gcc json-c libevent zlib coreutils
```
Then check:
```bash
verilator --version
riscv64-elf-gcc -march=rv32im -mabi=ilp32 -print-libgcc-file-name
```
The second command must print a path containing `rv32im` and ending in `libgcc.a`. If it does
not, the Homebrew compiler has no 32-bit libraries and the BIOS will not build. **Do not
start the agent; fix this first.** Alternatives: the `riscv-gnu-toolchain` Homebrew tap
(`riscv-software-src/riscv`, builds from source and takes about an hour), or a prebuilt
`riscv64-unknown-elf` toolchain. The compiler name must be one LiteX accepts, for example
`riscv64-unknown-elf-gcc` or `riscv64-elf-gcc`.

### 3. Set up Cline
- Provider: your local server (LM Studio or Ollama) with qwen3-coder-30b. Context window at least
  32k tokens, 64k if the memory allows.
- Auto-approve: only read-only actions (read files, list files). Approve every command that
  writes or deletes by hand, especially in Phases 2 and 6.
- Start **a new task for each phase**, so the context stays small.

### 4. Run the phases
In a new Cline task, send:

> Read /Users/davideriemma/Desktop/LITEX/agent-plan.md. Execute Phase N only, then stop.

| Phase | What happens | What you check |
|---|---|---|
| 1 | Inspect, make the backup zip | The zip exists and contains `minimal_soc.py` |
| 2 | Delete the old files | Review each `rm` before approving. The final `ls` matches the clean tree above |
| 3 | Check the installed tools | Versions look right; the `rv32im` check passes |
| 4 | Create the venv, install LiteX | `litex.__file__` is under `LITEX/litex/litex/` |
| 5 | **M0:** generate, build, simulate | The log shows `LiteX BIOS` / `litex>` |
| 6 | Git, rules, docs | `git status` is short; README and PLAN edits are correct |

Review carefully after phases **1, 2, 5 and 6**. Each Cline task ends with a line in
`output/M0_report.md`.

### 5. If the agent stops or gets stuck
- It stops by design at every **STOP**, and asks you a question. Read the error before answering.
- Do not let it fix `minimal_soc.py` or anything in `litex/`. If a fix is needed, either do it
  yourself or ask Claude Code to look at the error.
- A 30B model may repeat itself or drift in a long task. Cancel the task and restart the
  same phase from its first step: every step is safe to repeat except the `rm` commands of
  Phase 2 (a missing file is not an error) and `git init` (Phase 6).
- If the Phase 5 log stays empty, the simulator needs a real terminal. Run it by hand:
  ```bash
  source /Users/davideriemma/Desktop/LITEX/env.sh   # puts the venv and Homebrew on PATH
  cd /Users/davideriemma/Desktop/LITEX/output/architettura_minima
  ./minimal_soc.py --target sim --run
  ```
  Wait for the `litex>` prompt (a few minutes for the first build), then press `Ctrl-C` twice.

### 6. Close M0
- Open `output/M0_report.md` and `output/architettura_minima/build/sim/run.log`; confirm the
  `litex>` prompt.
- Review the diff of `output/README.md` and `output/PLAN.md` (`git diff` is empty before the
  first commit; use `git status` and open the files).
- Commit and tag:
  ```bash
  cd /Users/davideriemma/Desktop/LITEX
  git add -A && git commit -m "Clean baseline and M0" && git tag m0
  ```
- In `output/PLAN.md` §4, M0 is now met (the schedule dates in §7 stay as they are).

## What is not decided here
- The next step is M1 (Zephyr `hello_world` in simulation). It needs `west`, a Zephyr workspace
  and the Zephyr SDK, and should get its own plan after M0.
- The study and writing schedule in `output/PLAN.md` §7 is now behind (M0 was planned for
  22 Nov). Shift the dates, or ask Claude Code to regenerate the calendar.
