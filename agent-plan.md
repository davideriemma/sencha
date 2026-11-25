# agent-plan.md — Milestone M1: Zephyr `hello_world` on the minimal SoC in simulation

> Audience: a local coding agent (Cline with qwen3-coder-30b) on the user's Mac.
> The M0 version of this file is kept in git: `git show m0:agent-plan.md`.
> **Goal:** build Zephyr `hello_world` for the minimal SoC with the generated overlay, boot it in
> the Verilator simulation, and see `Hello World!` on the console. This also answers the open
> item "is 64 KiB of MAIN_RAM enough for `hello_world`".

## How to work (read this first, every task)

1. **Do only the phase you were asked to do.** Stop at the end of the phase and call
   `attempt_completion`. Do not start the next phase.
2. **One command per step.** Run the command exactly as written. Do not rewrite, shorten or
   "improve" it. Use absolute paths.
3. **Every step has Expected and If not.** If the output does not match **Expected**, do what
   **If not** says. Never invent a fix.
4. **STOP means:** call `ask_followup_question` with the failing command and the last 40 lines of
   its output, then wait. Do not try another approach.
5. **Show proof.** Never write "done" or "passed" unless the command output that proves it is in
   the conversation.
6. **Long commands run in the background** (marked **BACKGROUND**): start them as written, then
   poll the log with the given `tail` command every 60 seconds. Never wait for them in the
   foreground.
7. **Forbidden, always:**
   - `sudo`, `brew install`, `git commit`, `git push`, `git pull`, `git fetch`
   - editing anything under `/Users/davideriemma/Desktop/LITEX/litex/`
   - editing `minimal_soc.py`, or any file under `~/zephyrproject/`
   - deleting anything that is not created by this plan
   - editing other files except with the exact text given in this plan
8. **Report.** At the end of each phase append one line to
   `/Users/davideriemma/Desktop/LITEX/output/M1_report.md` (create it in Phase 1):
   `| Phase N | pass / fail / STOP | key output line |`.

## Context

| Item | Value |
|---|---|
| Project root (`$ROOT`) | `/Users/davideriemma/Desktop/LITEX` |
| Venv (LiteX + west + Zephyr requirements) | `/Users/davideriemma/.venvs/thesis` (Python 3.12.16) |
| Environment script | `$ROOT/env.sh` — puts Homebrew and the venv on `PATH` |
| Zephyr workspace | `/Users/davideriemma/zephyrproject` (outside the project, local disk) |
| Zephyr version | **v4.5.0** (pinned; released 2026-10-28) |
| Zephyr SDK | **1.0.1**, only the `riscv64-zephyr-elf` toolchain, in `/Users/davideriemma/zephyr-sdk-1.0.1` |
| Build output | `/Users/davideriemma/zephyr-build/hello` (outside the project) |
| Board | `litex_vexriscv` (`zephyr/boards/enjoydigital/litex_vexriscv`) |
| Overlay | `$ROOT/output/architettura_minima/build/sim/overlay.dts` (generated in M0; `overlay.config` is empty) |
| Existing tools | Homebrew, Verilator 5.054, riscv64-elf-gcc 16.2.0 (used by LiteX, not by Zephyr) |
| Out of scope | GateMate board, custom Zephyr board module, drivers, tests |

**How the boot works.** `minimal_soc.py --ram-init zephyr.bin` preloads the image into MAIN_RAM at
`0x4000_0000`. The BIOS then skips its memory test and jumps there.

---

## Phase 1 — Check prerequisites (read-only, plus the report file)

**1.1** The M0 baseline is in git and the tree is clean.
```bash
cd /Users/davideriemma/Desktop/LITEX && git tag && git status --short | wc -l && git log --oneline -1
```
Expected: `m0`, then `0`, then a commit line. If not: STOP.

**1.2** Homebrew tools needed by Zephyr.
```bash
for t in cmake gperf dtc ccache wget; do printf "%s: " $t; ls /opt/homebrew/bin/$t 2>&1; done; ls -d /opt/homebrew/opt/libmagic
```
Expected: five paths and `/opt/homebrew/opt/libmagic`.
If any is missing: STOP and tell the human to run
`brew install cmake gperf dtc ccache wget libmagic`.

**1.3** The M0 environment still works.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && python --version && verilator --version && which python
```
Expected: `Python 3.12.16`, `Verilator 5.054 ...`, and a path under `/Users/davideriemma/.venvs/thesis/`.
If not: STOP.

**1.4** The overlay from M0 exists.
```bash
ls -l /Users/davideriemma/Desktop/LITEX/output/architettura_minima/build/sim/overlay.dts && wc -c /Users/davideriemma/Desktop/LITEX/output/architettura_minima/build/sim/overlay.config
```
Expected: the file exists (about 1.6 KB) and `overlay.config` has `0` bytes.
If `overlay.dts` is missing, regenerate it (this is allowed):
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/Desktop/LITEX/output/architettura_minima && ./minimal_soc.py --target sim --no-compile 2>&1 | tail -3
```
If `overlay.config` is not empty: STOP (the build in 4.2 needs an extra argument).

**1.5** Network and disk.
```bash
curl -sI -m 15 https://github.com | head -1; df -h /Users/davideriemma | tail -1
```
Expected: `HTTP/2 200` (or a 301/302) and more than 15 GB available. If not: STOP.

**1.6** Create `/Users/davideriemma/Desktop/LITEX/output/M1_report.md` with exactly this content
(`write_to_file`), then add the Phase 1 line:
```markdown
# M1 report

| Phase | Result | Key output |
|---|---|---|
```

---

## Phase 2 — Zephyr workspace

**2.1** Install west in the venv.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && python -m pip install -q west && west --version
```
Expected: `West version: v1.x.x`. If not: STOP.

**2.2** Create the workspace on version v4.5.0.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.5.0 /Users/davideriemma/zephyrproject
```
Expected: ends with `=== Initial configuration done`. If the folder already exists: STOP.

**2.3 BACKGROUND** Download the modules. This takes 10–25 minutes and a few GB.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/zephyrproject && (nohup west update --narrow -o=--depth=1 > /Users/davideriemma/west-update.log 2>&1 &); sleep 2; echo started
```
Poll every 60 seconds:
```bash
tail -n 4 /Users/davideriemma/west-update.log; pgrep -fl "west update" | head -1
```
- **Done** when `pgrep` prints nothing.
- **Fail** if the log contains `fatal`, `error` or `Traceback` and `pgrep` prints nothing.
  Then STOP with the last 40 lines. (A network error can be retried once by running the
  same command again; `west update` resumes.)

**2.4** Check the result.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/zephyrproject && west list | wc -l && git -C zephyr describe --tags && ls zephyr/boards/enjoydigital/litex_vexriscv
```
Expected: a number above 20, `v4.5.0`, and the board files (`board.yml`, `litex_vexriscv.dts`, ...).
If not: STOP.

**2.5** Register Zephyr for CMake and install the Python requirements.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/zephyrproject && west zephyr-export && python -m pip install -q -r zephyr/scripts/requirements.txt && echo REQ_OK
```
Expected: ends with `REQ_OK`.
If `pip` fails: try once with the smaller file
`python -m pip install -q -r zephyr/scripts/requirements-base.txt`. If that fails too: STOP.

Add the Phase 2 line to the report, with the output of `west --version` and the Zephyr tag.

---

## Phase 3 — Zephyr SDK (RISC-V only)

**3.1** Look at the options of the installer; do not guess flags.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && west sdk install --help | grep -E "install-dir|gnu-toolchains|no-hosttools|version" | head
```
Expected: lines for `--install-dir`, `--gnu-toolchains`, `--no-hosttools`. If not: STOP.

**3.2 BACKGROUND** Install SDK 1.0.1 with only the RISC-V toolchain. No host tools: Homebrew
already provides `dtc`, `gperf` and `cmake`.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && (nohup west sdk install --version 1.0.1 --install-dir /Users/davideriemma/zephyr-sdk-1.0.1 --gnu-toolchains riscv64-zephyr-elf --no-hosttools > /Users/davideriemma/sdk-install.log 2>&1 &); sleep 2; echo started
```
Poll every 60 seconds:
```bash
tail -n 5 /Users/davideriemma/sdk-install.log; pgrep -fl "west sdk" | head -1
```
Done when `pgrep` prints nothing. It downloads about 140 MB.
If the log has an error and `pgrep` prints nothing: STOP with the last 40 lines.

**3.3** Check the compiler.
```bash
ls /Users/davideriemma/zephyr-sdk-1.0.1 && /Users/davideriemma/zephyr-sdk-1.0.1/gnu/riscv64-zephyr-elf/bin/riscv64-zephyr-elf-gcc --version | head -1
```
Expected: the SDK folder lists a `gnu` directory (older layout: `riscv64-zephyr-elf`), and the
compiler prints a version line.
If the compiler is not at that path: find it with
`find /Users/davideriemma/zephyr-sdk-1.0.1 -name 'riscv64-zephyr-elf-gcc' -type f | head -3`,
use that path, and write it in the report. If nothing is found: STOP.

**3.4** Add two lines at the end of `/Users/davideriemma/Desktop/LITEX/env.sh`
(`replace_in_file`: SEARCH the last line `source /Users/davideriemma/.venvs/thesis/bin/activate`,
REPLACE with these three lines):
```bash
source /Users/davideriemma/.venvs/thesis/bin/activate
export ZEPHYR_BASE=/Users/davideriemma/zephyrproject/zephyr
export ZEPHYR_SDK_INSTALL_DIR=/Users/davideriemma/zephyr-sdk-1.0.1
```
Check:
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && echo $ZEPHYR_BASE $ZEPHYR_SDK_INSTALL_DIR
```
Expected: the two paths.

Add the Phase 3 line to the report, with the compiler version.

---

## Phase 4 — Build `hello_world`

**4.1** Find the exact board name.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/zephyrproject/zephyr && west boards -n litex
```
Expected: a line `litex_vexriscv` (possibly more litex boards). If not: STOP.

**4.2 BACKGROUND** Build.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/zephyrproject/zephyr && (nohup west build -p always -b litex_vexriscv samples/hello_world -d /Users/davideriemma/zephyr-build/hello -- -DDTC_OVERLAY_FILE=/Users/davideriemma/Desktop/LITEX/output/architettura_minima/build/sim/overlay.dts > /Users/davideriemma/zephyr-build.log 2>&1 &); sleep 2; echo started
```
Poll every 30 seconds:
```bash
tail -n 6 /Users/davideriemma/zephyr-build.log; pgrep -fl "west build" | head -1
```
Done when `pgrep` prints nothing. A build takes 1–3 minutes.

**4.3** Check the result.
```bash
ls -l /Users/davideriemma/zephyr-build/hello/zephyr/zephyr.bin /Users/davideriemma/zephyr-build/hello/zephyr/zephyr.elf; grep -A6 "Memory region" /Users/davideriemma/zephyr-build.log | head -12
```
Expected: both files exist; the memory table lists the RAM usage.
**Copy the memory table (`RAM`, and `FLASH` if present) and the size of `zephyr.bin` into the
report.** These numbers answer the question about 64 KiB of MAIN_RAM.
- If `zephyr.bin` is larger than 65536 bytes (64 KiB) or the log says `region ... overflowed`:
  STOP (the SoC needs a larger MAIN_RAM; that is a decision for the human).

**4.4** If the build failed (no `zephyr.bin`), find the first error and choose the row:

| The log contains | Action |
|---|---|
| `Board ... not found`, `unknown board` | rerun 4.2 with `-b litex_vexriscv/litex_vexriscv` |
| `devicetree error`, `undefined node label`, `zephyr,entropy`, `prbs0` | STOP. Do **not** edit the overlay or Zephyr. Give the human the full error |
| `No such file ... overlay.dts` | go back to 1.4 |
| `Could not find a package configuration file ... Zephyr-sdk` or `toolchain` | check `echo $ZEPHYR_SDK_INSTALL_DIR` in the same shell, then STOP |
| `python`/`module not found` | STOP; name the module |
| anything else | STOP with the last 40 lines |

Add the Phase 4 line to the report, with the RAM usage and the size of `zephyr.bin`.

---

## Phase 5 — Boot in simulation (M1)

The first run rebuilds the simulator with the Zephyr image inside MAIN_RAM (about 2–3 minutes).
It overwrites the M0 log, so this run uses another log file.

**5.1 BACKGROUND** Run.
```bash
source /Users/davideriemma/Desktop/LITEX/env.sh && cd /Users/davideriemma/Desktop/LITEX/output/architettura_minima && (sleep 1500 | gtimeout 1500 python minimal_soc.py --target sim --run --ram-init /Users/davideriemma/zephyr-build/hello/zephyr/zephyr.bin > build/sim/zephyr_run.log 2>&1 &); sleep 2; echo started
```
Poll every 60 seconds, at most 20 times:
```bash
tail -n 8 /Users/davideriemma/Desktop/LITEX/output/architettura_minima/build/sim/zephyr_run.log
```
- **Pass** as soon as the log contains `Hello World!`.
- **Fail** if the log contains `Error`, `error:` or `Traceback`, or if the output stops changing
  for 10 checks.
- Seeing the LiteX BIOS banner first is normal; Zephyr starts after it
  (`*** Booting Zephyr OS build v4.5.0 ***`).

**5.2** Stop the simulation (always, pass or fail).
```bash
pkill -f "minimal_soc.py --target sim"; sleep 2; pgrep -fl "minimal_soc" | head -3
```
Expected: no output.

**5.3** Decide.
```bash
sed 's/\x1b\[[0-9;]*m//g' /Users/davideriemma/Desktop/LITEX/output/architettura_minima/build/sim/zephyr_run.log | grep -nE "Booting Zephyr|Hello World|Executing booted program|Memtest|litex>" | head
```
- A line with `Hello World!` → **M1 done**. Copy the matching lines into the report.
- Otherwise use the table, then STOP with
  `tail -n 40 .../build/sim/zephyr_run.log`:

| What you see | Likely cause (for the human; do not fix) |
|---|---|
| BIOS prompt `litex>`, no Zephyr output | the BIOS did not jump to the image (`ROM_BOOT_ADDRESS`) |
| `Executing booted program at 0x40000000` and nothing after | Zephyr crashed or hangs very early (wrong CSR address, console) |
| `*** Booting Zephyr ...` but no `Hello World!` for several minutes | the system tick floods the slow simulated CPU (1 MHz clock) |
| `file is too big` | the image does not fit in MAIN_RAM |

**5.4 Optional retry, only for the tick row above.** Rebuild with a slower tick, rerun 4.2 with
this extra argument at the end of the `-- ...` list, then repeat Phase 5:
```
-DCONFIG_SYS_CLOCK_TICKS_PER_SEC=100
```
Write in the report that this option was needed. Use it **only** if the log shows the
`*** Booting Zephyr` line without `Hello World!`.

Add the Phase 5 line to the report.

---

## Phase 6 — Reproducibility and docs

**6.1** Create `/Users/davideriemma/Desktop/LITEX/scripts/m1_build.sh` with exactly this content.
If you used the board name from the first row of 4.4 or the option from 5.4, put exactly that
in the file, and nothing else.
```bash
#!/usr/bin/env bash
# Build Zephyr hello_world for the minimal SoC (sim) with the generated overlay.
set -euo pipefail
source /Users/davideriemma/Desktop/LITEX/env.sh
cd "$ZEPHYR_BASE"
west build -p always -b litex_vexriscv samples/hello_world \
  -d "$HOME/zephyr-build/hello" -- \
  -DDTC_OVERLAY_FILE="$LITEX_ROOT/output/architettura_minima/build/sim/overlay.dts"
```

**6.2** Create `/Users/davideriemma/Desktop/LITEX/scripts/m1_run.sh` with exactly this content:
```bash
#!/usr/bin/env bash
# Boot the Zephyr image in the Verilator simulation. Usage: m1_run.sh [timeout_seconds]
set -uo pipefail
source /Users/davideriemma/Desktop/LITEX/env.sh
T="${1:-600}"
cd "$LITEX_ROOT/output/architettura_minima"
# The sleep keeps the simulator's stdin open; the log is also printed on screen.
sleep "$T" | gtimeout "$T" python minimal_soc.py --target sim --run \
  --ram-init "$HOME/zephyr-build/hello/zephyr/zephyr.bin" | tee build/sim/zephyr_run.log
```
Then make both executable:
```bash
chmod +x /Users/davideriemma/Desktop/LITEX/scripts/m1_build.sh /Users/davideriemma/Desktop/LITEX/scripts/m1_run.sh
```

**6.3** Check the build script really works (it rebuilds Zephyr, about 1–3 minutes). Run it in the
background like 4.2:
```bash
(nohup /Users/davideriemma/Desktop/LITEX/scripts/m1_build.sh > /Users/davideriemma/zephyr-build2.log 2>&1 &); sleep 2; echo started
```
Poll `tail -n 5 /Users/davideriemma/zephyr-build2.log; pgrep -fl "west build" | head -1`.
Expected: no error, and `/Users/davideriemma/zephyr-build/hello/zephyr/zephyr.bin` is newer than before
(`ls -l`). If not: STOP.

**6.4** Add the Zephyr versions to `/Users/davideriemma/Desktop/LITEX/.clinerules/project.md`
(`replace_in_file`). SEARCH:
```
| LiteX | 2026.08-213-gacbc4634e |
```
REPLACE (fill in the real values from Phases 2 and 3):
```
| LiteX | 2026.08-213-gacbc4634e |
| west | <version> |
| Zephyr | v4.5.0 (<output of git describe --tags>) |
| Zephyr SDK | 1.0.1, riscv64-zephyr-elf-gcc <version> |
```
And SEARCH:
```
- Simulate:      `cd output/architettura_minima && ./minimal_soc.py --target sim --run`
```
REPLACE:
```
- Simulate:      `cd output/architettura_minima && ./minimal_soc.py --target sim --run`
- Zephyr hello_world (M1): `scripts/m1_build.sh`, then `scripts/m1_run.sh` (Zephyr lives in ~/zephyrproject, SDK in ~/zephyr-sdk-1.0.1)
```

**6.5** Edit `/Users/davideriemma/Desktop/LITEX/output/README.md` (`replace_in_file`). SEARCH:
```
- Non eseguito: target `gatemate`, sintesi per la GateMate, build di Zephyr.
```
REPLACE — write what the report actually shows. If M1 passed:
```
- Eseguito (<today's date, dd/mm/yyyy>): build di Zephyr v4.5.0 `hello_world` per la board
  `litex_vexriscv` con l'overlay generato (SDK Zephyr 1.0.1) e avvio in simulazione Verilator:
  la console mostra `Hello World!` (M1). Immagine <size> byte, RAM usata <used> su 64 KiB
  di MAIN_RAM (script `scripts/m1_build.sh` e `scripts/m1_run.sh`).
- Non eseguito: target `gatemate` e sintesi per la GateMate.
```
If M1 did not pass, say in Italian which step failed instead of the first bullet.

**6.6** Edit `/Users/davideriemma/Desktop/LITEX/output/PLAN.md` (`replace_in_file`, three blocks).

Block 1 — SEARCH:
```
| Zephyr build with the generated overlay | Not run |
```
REPLACE (M1 passed; otherwise keep `Not run` and write `Failed: <reason>`):
```
| Zephyr `hello_world` build with the generated overlay | Done (Zephyr v4.5.0, SDK 1.0.1; <size> bytes, <used> of 64 KiB RAM) |
| Zephyr `hello_world` booted in simulation | Done: `Hello World!` on the console (M1, <date>) |
```

Block 2 — SEARCH:
```
`~/.venvs/thesis`). GateMate synthesis and the Zephyr build are the next steps.
```
REPLACE:
```
`~/.venvs/thesis`). Zephyr v4.5.0 and SDK 1.0.1 were installed on <date>. GateMate synthesis
and the custom Zephyr board module (M3) are the next steps.
```

Block 3 — SEARCH:
```
- [x] Rebuild the environment (venv, Verilator, RISC-V GCC). Zephyr SDK and `west` still to do.
```
REPLACE:
```
- [x] Rebuild the environment (venv, Verilator, RISC-V GCC, Zephyr SDK, `west`).
```
Block 4 — SEARCH:
```
- [ ] Build Zephyr `hello_world` with `build/sim/overlay.dts` (M1).
```
REPLACE:
```
- [x] Build Zephyr `hello_world` with `build/sim/overlay.dts` and boot it in simulation (M1).
```
(Use `[ ]` instead of `[x]` for anything that did not pass.)

**6.7** Final checks.
```bash
cd /Users/davideriemma/Desktop/LITEX && git status --short
```
Expected: only `.clinerules/project.md`, `agent-plan.md`, `env.sh`, `output/PLAN.md`, `output/README.md`,
`output/M1_report.md` and `scripts/`. Nothing from `~/zephyrproject` (it is outside the project).
Do **not** commit.

Add the Phase 6 line to the report.

---

## Final report

Print `/Users/davideriemma/Desktop/LITEX/output/M1_report.md`, then add under the table:
- versions: west, Zephyr (`git describe`), SDK, compiler,
- the RAM table and the size of `zephyr.bin`,
- the `Hello World!` line from `build/sim/zephyr_run.log`,
- any option used from 4.4 or 5.4,
- any STOP reached, with its error.

Then call `attempt_completion`. The human commits and tags `m1`.
