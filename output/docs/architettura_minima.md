# Architettura minima della piattaforma (bozza di paragrafo)

> Bozza per la tesi. Le parti marcate **[da verificare]** non sono ancora state
> confermate da una prova e vanno controllate prima della stesura definitiva.

## 1. Contesto e criterio di scelta

LiteX è un framework open source per la costruzione di System-on-Chip su FPGA: il SoC
viene descritto in Python (Migen) e il framework genera il Verilog, la mappa dei
registri e il software di base (BIOS). La versione di riferimento per questo lavoro è
la 2026.08. Il grado di configurabilità è molto elevato: CPU, bus di sistema, memorie
e periferiche sono tutti parametri. Per questo, prima di sviluppare il Board Support
Package (BSP) per Zephyr, è stato necessario fissare un'architettura di riferimento.

L'architettura è stata scelta con tre criteri:

1. **Minimalità.** Contiene solo ciò che Zephyr richiede per avviarsi e stampare su
   console: una CPU supportata, una RAM in cui eseguire, un timer per il tick di
   sistema, una UART e un controllore per il reset.
2. **Identità tra simulazione e scheda.** La stessa definizione viene istanziata sia in
   simulazione (Verilator) sia sulla scheda Olimex GateMate A1-EVB. Mappa di memoria,
   registri e interrupt coincidono; cambiano solo la frequenza di clock e i pin. Il BSP
   sviluppato in simulazione resta quindi valido sulla scheda.
3. **Estendibilità.** Il bus di sistema è Wishbone, uno dei due standard (con AXI)
   richiesti dal Bus Firewall, e lascia un punto di innesto esplicito per gli IP core
   di sicurezza previsti nelle fasi successive.

## 2. Componenti

La Figura (file `component_diagram.svg`, copia `component_diagram.png`, sorgente
`component_diagram.puml`) riporta il
diagramma dei componenti UML. I componenti sono i seguenti.

| Componente | Ruolo | Configurazione |
|---|---|---|
| VexRiscv | CPU soft-core RISC-V a 32 bit | variante `standard`: RV32IM, cache istruzioni e dati, 32 linee di interrupt, reset a `0x0000_0000` |
| Bus Wishbone | Bus di sistema | 32 bit dati, 32 bit indirizzi; interconnessione condivisa con arbitro, decodificatore e timeout |
| ROM | Memoria di boot | 128 KiB a `0x0000_0000`, contiene il BIOS LiteX |
| SRAM | RAM del BIOS | 8 KiB a `0x1000_0000`, stack e dati del BIOS |
| MAIN_RAM | RAM applicativa | 64 KiB a `0x4000_0000`, vi viene caricata ed eseguita l'immagine Zephyr |
| Wishbone2CSR | Ponte verso i registri | regione CSR di 64 KiB a `0xF000_0000`, registri a 32 bit |
| SoCController (`ctrl`) | Reset software, registro di prova, contatore errori di bus | `0xF000_0000` |
| Identifier | Stringa identificativa del SoC | `0xF000_0800` |
| Timer (`timer0`) | Tick di sistema | `0xF000_1000`, IRQ 1, con contatore di uptime a 64 bit |
| UART (`uart`) | Console | `0xF000_1800`, IRQ 0, 115200 baud |
| CRG | Clock e reset | 1 MHz in simulazione, 24 MHz (PLL) sulla GateMate A1-EVB |

Le scelte non ovvie sono tre.

- **Variante `standard` della CPU.** È la configurazione attesa dalla board
  `litex_vexriscv` di Zephyr (`litex,vexriscv-standard`).
- **Timer con uptime.** Il driver del timer LiteX in Zephyr legge i registri
  `uptime_latch` e `uptime_cycles`; senza questa opzione (`timer_uptime`) il device tree
  generato non li contiene e il driver non può funzionare.
- **MAIN_RAM integrata da 64 KiB.** Zephyr su LiteX viene eseguito interamente in RAM a
  partire da `0x4000_0000`. La dimensione è stata scelta per restare entro la block RAM
  della GateMate A1 (circa 160 KiB complessivi, da condividere con ROM e SRAM)
  **[da verificare con la sintesi]** e deve bastare per l'applicazione `hello_world`
  **[da verificare]**. In simulazione può essere aumentata con `--main-ram-size`.

## 3. Lavoro svolto

1. **Installazione di LiteX** sulla macchina di sviluppo, con l'ecosistema di core
   (LiteDRAM, LiteEth, ecc.) e i pacchetti delle CPU.
2. **Prima compilazione di un sistema minimale** (VexRiscv, ROM con BIOS, SRAM, UART) a
   partire dal target della Sipeed Tang Primer 20K. La generazione del SoC e la
   compilazione del BIOS sono andate a buon fine (BIOS di 27,6 KiB); la sintesi si è
   fermata nella toolchain proprietaria Gowin per un errore di verifica della licenza.
3. **Passaggio alla simulazione** con `litex_sim` (Verilator), dove lo stesso sistema
   minimale è stato compilato e avviato fino al prompt del BIOS. La simulazione elimina
   la dipendenza dalla toolchain del produttore e dal flashing e accorcia in modo
   significativo il ciclo di sviluppo.
4. **Definizione dell'architettura minima** in uno script dedicato
   (`architettura_minima/minimal_soc.py`). Un unico dizionario di parametri descrive
   l'architettura e viene applicato a due target, `sim` e `gatemate`. Lo script produce
   il Verilog, la mappa dei registri (`csr.json`, `csr.csv`) e l'overlay per Zephyr.
5. **Generazione dell'overlay Zephyr** (`overlay.dts`, `overlay.config`) tramite lo
   strumento `litex_json2dts_zephyr` di LiteX, a partire dalla mappa dei registri.

Lo stato attuale della verifica è il seguente. Lo script è stato eseguito per entrambi
i target fino alla generazione del Verilog e dell'overlay: le due mappe dei registri
differiscono solo per nome della piattaforma, identificativo e frequenza di clock.
L'avvio in simulazione della nuova architettura e la compilazione di Zephyr **non sono
ancora stati eseguiti** e costituiscono il passo successivo.

## 4. Dal SoC al BSP Zephyr

Il flusso previsto è:

```
minimal_soc.py ──> csr.json ──> litex_json2dts_zephyr ──> overlay.dts + overlay.config
                                                                 │
        west build -b litex_vexriscv <app> -DDTC_OVERLAY_FILE=overlay.dts
                                                                 │
                                                            zephyr.bin
```

L'overlay ridefinisce, rispetto al device tree predefinito della board `litex_vexriscv`,
gli indirizzi dei registri di `ctrl`, `uart` e `timer0`, i numeri di interrupt, la
frequenza di clock e la regione di RAM, e disabilita le periferiche assenti (Ethernet,
SPI, I2C, SD, watchdog). L'immagine `zephyr.bin` viene poi:

- in simulazione, precaricata in MAIN_RAM e avviata dal BIOS
  (`minimal_soc.py --target sim --run --ram-init zephyr.bin`);
- sulla scheda, caricata via seriale dal BIOS
  (`litex_term /dev/ttyUSBX --speed 115200 --kernel zephyr.bin`).

## 5. Estensioni previste

Lo sviluppo procede in modo incrementale: a ogni passo si aggiunge un componente
hardware e il relativo supporto software in Zephyr.

1. **Bus Firewall** tra i master Wishbone della CPU e l'interconnessione, con interfaccia
   di configurazione nella regione CSR.
2. **IP core OpenTitan**, collegati tramite un adattatore da Wishbone a TL-UL (il bus
   usato dagli IP OpenTitan, non supportato nativamente da LiteX). La selezione degli IP
   è discussa in `opentitan_panoramica.md`.
