# OpenTitan: panoramica dei componenti di sicurezza

> Documento di lavoro per la scelta degli IP core da integrare nella piattaforma LiteX.
> Fonti: documentazione ufficiale OpenTitan (elenco degli IP in `hw/ip` e pagina di
> progetto del top level Earl Grey, ramo `master`), consultate il 16/11/2026. Le
> valutazioni sull'integrazione in LiteX (sezioni 4 e 5) sono stime e non risultati
> di prove.

## 1. Che cos'è OpenTitan

OpenTitan è un progetto open source, coordinato da lowRISC, che realizza un *silicon
root of trust*: un chip che fa da radice di fiducia per l'avvio sicuro, l'identità del
dispositivo e la custodia delle chiavi. Il progetto pubblica l'RTL in SystemVerilog, la
verifica, il software di base e la documentazione, con licenza Apache 2.0.

Il top level di riferimento è **Earl Grey**. Il ramo `master` descrive oggi Earl Grey 2
(memoria non volatile RRAM, gestore di chiavi DPE); il progetto già realizzato su
silicio è nel ramo `earlgrey_1.0.0` (memoria flash, controllore OTP dedicato). I nomi di
alcuni blocchi cambiano tra le due versioni, come indicato nelle tabelle.

Tre caratteristiche rendono gli IP riutilizzabili fuori da Earl Grey:

- **Interfaccia uniforme ("comportable IP").** Ogni IP espone i registri su bus
  TL-UL (TileLink Uncached Lightweight), più interrupt e segnali di *alert*.
- **Registri descritti in Hjson.** Da un'unica descrizione vengono generati RTL dei
  registri, header C e documentazione.
- **Contromisure dichiarate.** Molti blocchi includono protezioni contro attacchi a
  canale laterale (SCA) e a iniezione di guasti (FI).

## 2. IP di sicurezza

### 2.1 Acceleratori crittografici

| IP | Funzione | Note di sicurezza |
|---|---|---|
| `aes` | Cifratura e decifratura AES a 128, 192, 256 bit | Contromisure SCA e FI (mascheramento); GCM non è in hardware |
| `hmac` | SHA-2 (256/384/512) e HMAC | Nessun mascheramento |
| `kmac` | SHA-3, SHAKE, cSHAKE e KMAC | Nucleo Keccak mascherato al primo ordine; usato anche come funzione di derivazione delle chiavi |
| `otbn` | Coprocessore programmabile per crittografia asimmetrica (RSA, ECC, post-quantum ML-DSA e ML-KEM) | Contromisure SCA e FI; memorie proprie (16 KiB istruzioni, 32 KiB dati) |
| `ascon` | Cifratura autenticata Ascon (crittografia leggera) | Blocco recente, presente nell'elenco degli IP |

### 2.2 Catena dell'entropia

| IP | Funzione |
|---|---|
| `entropy_src` | Filtra e controlla (health test) i bit grezzi di una sorgente di rumore fisica |
| `csrng` | Generatore di numeri casuali crittograficamente sicuro, alimentato da `entropy_src` |
| `edn` | Distribuisce i numeri casuali di `csrng` agli altri blocchi hardware |

Su FPGA la sorgente di rumore è emulata (comportamento simile a un PRBS): la catena è
funzionale ma non fornisce entropia reale.

### 2.3 Chiavi, identità e ciclo di vita

| IP | Funzione |
|---|---|
| `keymgr_dpe` (Earl Grey 2) / `keymgr` (1.0) | Deriva chiavi di identità, attestazione e *sealing* senza esporre i segreti al software; può consegnare le chiavi direttamente ad AES, HMAC, KMAC e OTBN (*sideload*) |
| `lc_ctrl` | Gestisce gli stati del ciclo di vita del dispositivo (test, produzione, RMA, scrap) e abilita di conseguenza debug, memoria non volatile e gestore di chiavi |
| `rv_dm`, `soc_dbg_ctrl` | Modulo di debug RISC-V e controllo dell'accesso di debug, subordinati al ciclo di vita |

### 2.4 Memorie protette

| IP | Funzione |
|---|---|
| `rom_ctrl` | ROM di boot cifrata (*scrambled*); al reset ne calcola il digest con KMAC e blocca l'avvio se non coincide |
| `sram_ctrl` | SRAM con cifratura leggera, controllo di integrità e cancellazione sicura |
| `rram_ctrl` (Earl Grey 2) / `flash_ctrl` (1.0) | Memoria non volatile con protezione per pagina, cifratura al volo e cancellazione sicura |
| `otp_ctrl` (1.0) / `otp_macro` | Memoria programmabile una sola volta: segreti radice, stato del ciclo di vita, chiavi per la cifratura delle memorie |

### 2.5 Rilevamento e reazione

| IP | Funzione |
|---|---|
| `alert_handler` | Raccoglie gli *alert* di tutti i blocchi, li classifica e, se il software non reagisce, avvia una risposta hardware a più stadi (fino al reset o allo stato di scrap). È generato per ogni top level, non compare nell'elenco di `hw/ip` |
| `sensor_ctrl` | Interfaccia verso i sensori analogici (tensione, clock, temperatura) e inoltro dei relativi alert |
| `aon_timer` | Timer di risveglio e watchdog su clock sempre attivo |

### 2.6 CPU

Earl Grey usa il core **Ibex** in configurazione *SecureIbex*: protezione fisica della
memoria estesa (Smepmp, 16 regioni), due core in *lockstep* per rilevare i guasti,
controlli di integrità su register file, cache istruzioni e interfacce di bus, program
counter protetto.

## 3. Altri IP (non di sicurezza)

`uart`, `spi_host`, `spi_device`, `i2c`, `i3c`, `usbdev`, `rv_timer`, `pattgen`,
`adc_ctrl`, `sysrst_ctrl`, `dma`, `mbx`. Per queste funzioni LiteX offre già core
propri con driver Zephyr esistenti (`litex,uart`, `litex,spi`, `litex,i2c`,
`litex,timer0`, `litex,watchdog`): non conviene sostituirli.

## 4. Vincoli di integrazione in LiteX

1. **Bus.** Gli IP parlano TL-UL; LiteX offre Wishbone, AXI, AXI-Lite e AHB e non
   supporta TL-UL. Per questo gli IP non vengono collegati al bus dell'host: stanno nella
   RoT dedicata, su una crossbar TL-UL interna, e LiteX istanzia la RoT come blocco unico
   (`rot_stato_arte_architettura.md`, §4.3). Non serve quindi un adattatore
   Wishbone → TL-UL.
2. **Linguaggio e primitive.** L'RTL è SystemVerilog e dipende dalla libreria di
   primitive `prim` di OpenTitan. LiteX può istanziare moduli esterni, ma la toolchain
   deve accettare SystemVerilog: per la GateMate (flusso Yosys) può servire una
   conversione preventiva (ad esempio `sv2v`) **[da verificare]**; in simulazione
   Verilator lo supporta.
3. **Dipendenze tra blocchi.** Pochi IP sono autonomi. AES e KMAC chiedono casualità a
   EDN per il mascheramento; il gestore di chiavi richiede KMAC, il ciclo di vita e la
   memoria OTP; quasi tutti emettono alert e ricevono segnali dal ciclo di vita. Usati
   da soli, questi ingressi vanno collegati a valori fissi, rinunciando alla relativa
   protezione.
4. **Risorse.** La GateMate A1 ha circa 20 000 elementi logici **[da verificare]**:
   OTBN e gli acceleratori mascherati difficilmente trovano posto accanto al SoC. AES
   prevede un parametro per disattivare il mascheramento e ridurre l'area.
5. **Software.** Zephyr include una board Earl Grey con driver per alcune periferiche
   OpenTitan; la copertura per gli acceleratori crittografici va verificata
   **[da verificare]**. Per ogni IP integrato va previsto un driver o un binding.

## 5. Selezione degli IP

La selezione e l'ordine di integrazione degli IP seguono le fasi della RoT dedicata
descritte in `rot_stato_arte_architettura.md` (§4.3). La proposta precedente, che
prevedeva gli IP sul bus dell'host tramite un adattatore Wishbone → TL-UL, è conservata
nel tag git `m0`.

## 6. Alternative già presenti in LiteX

- **VexRiscv `secure`.** Variante della CPU con protezione fisica della memoria (PMP,
  16 regioni) e modalità utente. Permetterebbe l'isolamento in Zephyr senza IP esterni;
  la compatibilità con la board `litex_vexriscv`, che dichiara la variante `standard`,
  è **[da verificare]**.
- **Ibex.** LiteX supporta Ibex come CPU, ma il supporto Zephyr per LiteX è definito
  per VexRiscv: cambiare CPU significherebbe scrivere un nuovo SoC in Zephyr.
  Nell'architettura attuale Ibex non esegue Zephyr: è la CPU della RoT ed esegue solo
  il suo firmware, mentre Zephyr resta su VexRiscv.
- **Bus Firewall.** Agisce sul bus Wishbone ed è complementare a PMP: il PMP limita ciò
  che il software può indirizzare, il firewall filtra le transazioni di ogni master.
