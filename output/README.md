# Contenuto della cartella

**Materiale per la tesi (novembre 2026)**

| Percorso | Contenuto |
|---|---|
| `docs/architettura_minima.md` | Bozza del paragrafo: architettura minima e lavoro svolto |
| `docs/component_diagram.svg` / `.png` | Diagramma dei componenti UML |
| `docs/component_diagram.puml` | Sorgente PlantUML dello stesso diagramma |
| `docs/opentitan_panoramica.md` | Panoramica degli IP di sicurezza OpenTitan e proposta di selezione |
| `PLAN.md` | Piano in inglese: sintesi del lavoro, studio di Zephyr e OpenTitan, sviluppo agentico, calendario giornaliero 21 nov – 15 dic |
| `architettura_minima/minimal_soc.py` | Definizione del SoC minimo (target `sim` e `gatemate`) |
| `architettura_minima/build/<target>/` | Verilog, `csr.json`, `csr.csv`, overlay Zephyr generati dallo script |

## Uso dello script

```
cd architettura_minima
./minimal_soc.py --target sim --run                        # BIOS LiteX in simulazione
./minimal_soc.py --target sim --run --ram-init zephyr.bin  # avvio diretto di Zephyr
./minimal_soc.py --target gatemate --run                   # sintesi per Olimex GateMate A1-EVB
./minimal_soc.py --target sim --no-compile                 # solo Verilog, CSR e overlay
```

Compilazione di Zephyr con l'overlay generato:

```
west build -b litex_vexriscv samples/hello_world -DDTC_OVERLAY_FILE=<...>/build/sim/overlay.dts
```

## Stato della verifica

- Eseguito (23/11/2026): generazione di Verilog, mappa CSR e overlay per il target `sim`;
  compilazione del BIOS e simulazione Verilator fino al prompt `litex>` (M0). Il test di
  memoria su MAIN_RAM (64 KiB) è riuscito. Ambiente: macOS, Verilator 5.054,
  riscv64-elf-gcc 16.2.0, Python 3.12 in `~/.venvs/thesis`.
- Non eseguito: target `gatemate`, sintesi per la GateMate, build di Zephyr.
