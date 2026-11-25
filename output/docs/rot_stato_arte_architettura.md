# RoT dedicata per SoC a basso costo: stato dell'arte, architettura e obiettivi

> Documento di lavoro per la tesi, 24/11/2026. Diagramma: `component_diagram_rot.svg`
> (sorgente `component_diagram_rot.puml`). Nome del SoC provvisorio: **Sencha** (§4.1).
>
> Convenzione sulle fonti: **[V]** verificata su pagina o articolo, **[S]** solo da estratti
> di ricerca, **[da verificare]** non confermata. Le stime di area e di costo non marcate
> sono ragionamenti, non misure.

## 1. Obiettivi della trattazione

Si vuole dimostrare che una **RoT attiva e dedicata**, oggi propria di prodotti costosi
(server, smartphone, Chromebook), si può offrire a **costo marginale quasi nullo** su
FPGA e con **costo di integrazione software quasi nullo** per chi sviluppa con Zephyr.

Obiettivi misurabili:

| # | Obiettivo | Evidenza attesa |
|---|---|---|
| O1 | Generatore unico (LiteX/Python) che produce SoC, RoT, chiavi, immagini firmate, board Zephyr | Un comando: bitstream + `zephyr.signed.bin` avviabile |
| O2 | Secure boot attivo: l'host parte solo se la RoT ha verificato l'immagine | Test negativo: immagine alterata o rollback → host resta in reset |
| O3 | Isolamento: nessun percorso dall'host alla memoria della RoT | Analisi della netlist e test sul link: solo comandi ammessi |
| O4 | Integrazione Zephyr a costo zero | `hello_world` e un esempio di rete ricompilati senza modifiche al codice |
| O5 | Servizi runtime via API PSA standard (RNG, firma, attestazione) | Esempio Zephyr che usa `psa_*` con chiave che non esce dalla RoT |
| O6 | Costo quantificato | LUT/BRAM della RoT su GateMate rispetto al SoC host e al dispositivo |

## 2. Stato dell'arte

### 2.1 Tassonomia delle soluzioni

| Classe | Esempi | Attiva (blocca il boot)? | Isolata dall'host? | Aperta? | Costo |
|---|---|---|---|---|---|
| TPM discreto | Infineon SLB9672, ST | No: registra misure, non impedisce l'esecuzione | Sì (chip separato), ma bus in chiaro | No | ≈ 3–7 $ a pezzo [S] |
| Secure element | Microchip ATECC608B, NXP SE050 | No: funzioni fisse a richiesta | Sì | No | ≈ 0,8–2 $ [S] |
| RoT integrata condivisa (fTPM, TEE) | Intel PTT/CSME, AMD fTPM, TrustZone | Parziale | No: condivide core, cache, alimentazione | No | "gratis" in BOM |
| RoT attiva dedicata | Google Titan/OpenTitan, Caliptra, MS Cerberus, Lattice MachXO3D/Mach-NX, Apple SEP | Sì | Sì | OpenTitan e Caliptra sì | Alta (die/chip dedicato, ≈ 8–21 $ MachXO3D [S]) |
| Ricerca accademica | HECTOR-V, Sancus, SMART, TrustLite, TIMBER-V | Varia | Varia | Sì | Overhead di area (§2.5) |

### 2.2 Limiti del TPM discreto

- **È passivo.** La radice di misura (CRTM) è nel firmware dell'host. Il TPM registra ciò
  che si è avviato, ma non può tenere la CPU in reset né impedire l'esecuzione di codice
  non firmato. Fonti: architettura TCG TPM 2.0, Part 1; IoT World Today [S].
- **Il bus è attaccabile.** I collegamenti LPC, SPI e I2C sono in chiaro.
  - TPM Genie, interposer su I2C (NCC Group, 2018) [V].
  - Estrazione della chiave BitLocker da LPC con un FPGA da ≈ 30 $ (Andzakovic, 2019) [V].
  - Estrazione della stessa chiave da SPI (WithSecure) [V].
  - Le sessioni cifrate (*parameter encryption*) proteggono solo il primo parametro, sono
    opzionali e vanno attivate dall'host [V]. Il TCG ha una bozza di linee guida contro
    gli interposer attivi (RC1, maggio 2026) [S].
- **Difetti di implementazione non correggibili.**
  - TPM-Fail: chiavi ECDSA recuperate per timing da un TPM ST e dall'fTPM Intel
    (USENIX Security 2020) [V].
  - ROCA: chiavi RSA deboli generate dai chip Infineon (ACM CCS 2017, CVE-2017-15361) [V].
  - Su silicio fisso si può solo sostituire il chip.
- **Inadatto alle MCU.** Costo, area su PCB e complessità dello stack software (TSS) sono
  sproporzionati per dispositivi piccoli [S].

### 2.3 Limiti delle RoT integrate o condivise

- **Risorse condivise, quindi canali laterali e guasti indotti.**
  - faulTPM: glitch di tensione sull'AMD-SP espone l'intero stato dell'fTPM con ≈ 200 $
    di hardware (2023, CVE-2023-20589) [V].
  - CLKSCREW (USENIX Security 2017) e VoltJockey (CCS 2019): fault injection *da
    software* tramite DVFS contro TrustZone [V].
  - ARMageddon (USENIX Security 2016) e TruSpy (2016): le cache condivise rivelano lo stato
    del mondo sicuro [V].
- **TCB grande e chiuso.** Il SoK di Cerdeira et al. (IEEE S&P 2020) analizza 207
  vulnerabilità dei TEE TrustZone [V]. CVE-2019-0090 è un difetto nella mask ROM di Intel
  CSME, non correggibile su silicio esistente [V].
- **Il contro-argomento.** L'integrazione on-die (Microsoft Pluton) elimina il bus
  attaccabile del TPM discreto [V]. La nostra architettura deve quindi proteggere il link
  (§4.4) per non reintrodurre il problema.

### 2.4 Perché la RoT attiva e dedicata è la scelta "pregiata"

- **NIST SP 800-193** (Platform Firmware Resiliency, 2018) organizza la resilienza del
  firmware in protezione, rilevamento e ripristino. Richiede una RoT capace di *agire*,
  non solo di misurare [S].
- **Isolamento architetturale.**
  - HECTOR-V (AsiaCCS 2021) argomenta che i TEE a core condiviso sono difficili da rendere
    immuni ai canali laterali. Propone quindi un core sicuro separato con monitor dei
    bus [V].
  - Il secure element OpenTitan (arXiv 2406.11558, 2024) non ha porte slave accessibili
    all'host: comunica solo tramite mailbox [V].
- **Certificazione.**
  - PSA Certified L2 richiede l'isolamento tra mondo sicuro e non sicuro.
  - L3 aggiunge la resistenza ad attaccanti fisici.
  - Un secure element già certificato può fare da sottosistema RoT pre-certificato [S].
- **Trasparenza.** OpenTitan (2019) e Caliptra (OCP/CHIPS Alliance) rendono pubblico
  l'RTL: la sicurezza si verifica e non si presume [V]. Caliptra dichiara un perimetro
  "deliberatamente minimale" [S]. È la stessa filosofia che adottiamo per la RoT ridotta.

### 2.5 Impatto sul costo

**Area su silicio: OpenTitan Earl Grey.** Report di sintesi ASIC dell'8/3/2024, in kGE,
nodo non dichiarato [V].

| Blocco | kGE | Nella nostra RoT |
|---|---|---|
| Top level (`top_earlgrey`) | 3878 | — |
| Ibex con macro (core nudo 57 kGE, 81 con PMP [S]) | 264 | Sì |
| HMAC | 74 | Sì |
| ROM ctrl | 63 | Fase 2 |
| OTP ctrl (di cui 285 di macro) | 403 | Emulato |
| keymgr | 87 | Fase 3 |
| AES (versione Earl Grey, mascherata) | 114 | Fase 3, senza mascheramento |
| KMAC (mascherato) | 479 | No |
| OTBN | 394 | No |
| Main SRAM ctrl (di cui 724 di macro) | 741 | Ridotta |

- **I blocchi esclusi pesano molto.** KMAC e OTBN valgono da soli ≈ 873 kGE, cioè ≈ 22 %
  del top level. Con AES si arriva a ≈ 25 %. Le memorie dominano il resto.
- **Il costo di una RoT discende soprattutto da due scelte:** quali acceleratori
  asimmetrici e mascherati includere, e quanta memoria privata dare alla RoT.
- **Ordini di grandezza su silicio reale.**
  - In GF 22FDX OpenTitan occupa ≈ 1,7 mm², ≈ 30 % di un SoC di prova da 7,3 mm²
    (arXiv 2406.11558) [V].
  - Caliptra 2.1 conta ≈ 1,64 Mgate, di cui ≈ 62 % in acceleratori e key vault [S].

**Area su FPGA: HECTOR-V** [V]. Su Kintex-7 il core sicuro separato aggiunge il 14,8 % di
LUT a una piattaforma di 55 443 LUT:

| Componente | LUT |
|---|---|
| RI5CY | 5780 |
| Crossbar AXI4 | 3052 |
| Monitor di sicurezza | 446 |

Per un host piccolo come il nostro l'overhead *relativo* sarà ben più alto. È il dato
chiave da misurare (O6).

**Costo in BOM (prezzi di distributori, indicativi)** [S]:

| Dispositivo | Prezzo |
|---|---|
| ATECC608B | ≈ 0,8–0,9 $ |
| TPM SLB9672 | ≈ 3–7 $ |
| Lattice MachXO3D (RoT su FPGA) | ≈ 8 $ (200+ pezzi), ≈ 21 $ (1 pezzo) |

A questi si aggiungono area su PCB, montaggio e collaudo (Analog Devices AN-2604) [S].

**Lacune ancora da colmare** [da verificare]:
- costi di certificazione (CC, FIPS 140-3, SESIP);
- rapporto di area tra versione mascherata e non mascherata;
- kGE di AES, SHA-256 e P-256 standalone;
- analisi economiche peer-reviewed sul costo della sicurezza nell'IoT.

## 3. Il vuoto che il progetto colma

Nessuna delle classi del §2.1 soddisfa insieme i quattro requisiti seguenti:

1. RoT **attiva**: tiene l'host in reset fino alla verifica.
2. RoT **isolata**: core, memoria e bus propri.
3. Costo **marginale ≈ 0** su prodotti che hanno già un FPGA: solo LUT e BRAM, nessun chip
   in più in BOM.
4. Integrazione software **trasparente** per un RTOS diffuso: API PSA, MCUboot, board
   generata.

OpenTitan soddisfa i primi due, ma è dimensionato per ASIC e FPGA grandi (CW310, Kintex-7)
e non offre un percorso "porta la tua app Zephyr". Lattice MachXO3D è una RoT attiva su
FPGA, ma è chiusa e pensata per i server. HECTOR-V è vicino come architettura, ma non
affronta l'integrazione software né il costo su FPGA piccoli.

## 4. Proposta

### 4.1 Nome

| Nome | Motivazione |
|---|---|
| **Sencha** (consigliato) | I top level OpenTitan hanno nomi di tè (Earl Grey, English Breakfast, Darjeeling); il sencha è un tè verde "leggero": dichiara la parentela e la versione ridotta |
| LiteWarden | Richiama LiteX e la funzione di guardiano |
| Matcha | Stessa famiglia tematica, meno legato al concetto di leggerezza |

Prima della scelta definitiva va controllato che il nome non sia già in uso
[da verificare].

### 4.2 Applicazioni a costo contenuto

Il caso più forte è quello dei **prodotti che hanno già un FPGA**, dove la RoT costa solo
risorse logiche:

- **Strumentazione e acquisizione dati.** ADC esterni su SPI, firmware aggiornabile sul
  campo, dati che devono essere autentici: banchi di prova, analizzatori di potenza,
  oscilloscopi entry-level.
- **Controllo industriale e motion control.** PLC compatti e azionamenti con FPGA per PWM
  ed encoder, aggiornamenti OTA e Ethernet di campo, requisiti IEC 62443 e Cyber
  Resilience Act.
- **Gateway e nodi edge.** Contatori intelligenti, colonnine di ricarica, automazione di
  edifici: firmware firmato, anti-rollback, attestazione verso il cloud.
- **Telecamere e SDR.** Pipeline già su FPGA, con secure boot e identità del dispositivo
  senza secure element aggiuntivo.
- **Ricerca e didattica.** Una piattaforma aperta per sperimentare secure boot,
  attestazione e attacchi.

La traduzione in termini FPGA (LUT/BRAM, dispositivo minimo, € per unità) si farà a SoC
generato (O6).

### 4.3 RoT (dominio Ibex, IP OpenTitan)

| IP | Ruolo | Fase | Motivazione |
|---|---|---|---|
| Ibex (RV32IMC, PMP) | CPU della RoT | 1 | È il core di OpenTitan; parla TL-UL nativamente |
| Crossbar TL-UL | Interconnessione interna | 1 | Riusa gli IP **senza** adattatori Wishbone→TL-UL |
| Boot ROM | Codice immutabile, verifica la firma in SW (Ed25519 o ECDSA-P256) | 1 | `rom_ctrl` (digest via KMAC) rinviato: KMAC è il blocco più grande |
| `sram_ctrl` | SRAM privata | 1 | Scrambling opzionale |
| `hmac` | SHA-256 / HMAC | 1 | Accelera l'hash dell'immagine; nessuna dipendenza da EDN |
| `otp_ctrl` emulato | Hash della chiave pubblica, contatore anti-rollback, stato LC | 1 | Su FPGA: semantica solo 0→1 imposta in logica, persistenza in flash |
| `lc_ctrl` ridotto | DEV / PROD / RMA, abilita o disabilita il debug | 1 | Senza ciclo di vita il debug resta una backdoor |
| `spi_device` | Link verso l'host: modo TPM (mailbox) + flash passthrough | 1 | Un solo IP fa da mailbox e da filtro sulla flash |
| `spi_host` | Master unico della SPI flash | 1 | La RoT legge e verifica l'immagine prima dell'host |
| `gpio` / `rstmgr` | HOST_RST_N, ROT_IRQ | 1 | Reset gating: la RoT è attiva, non passiva |
| `rv_timer`, `aon_timer` | Tick e watchdog | 1 | Recupero da stalli |
| `entropy_src`, `csrng`, `edn` | RNG | 2 | Su FPGA la sorgente è emulata: serve un TRNG a ring oscillator validato |
| `alert_handler` ridotto | Reazione HW agli alert | 2 | |
| `keymgr`, `aes` | Identità del dispositivo, sealing, cifratura del link | 3 | |
| `otbn` | ECC/RSA/PQC accelerati | Escluso | ≈ 394 kGE e 48 KiB di memoria propria: non sta sulla GateMate |

**Scelta di architettura.** La RoT si costruisce come piccolo top level TL-UL, sul modello
di `top_englishbreakfast`, la versione ridotta di Earl Grey [da verificare]. LiteX la
istanzia come **un solo blocco** con le sole porte del link. Ne seguono due conseguenze:

- l'adattatore Wishbone→TL-UL previsto nel `PLAN.md` non serve più per la RoT;
- l'isolamento si ottiene *per costruzione*: tra i due domini non esiste alcun bus.

### 4.4 Chip principale (dominio VexRiscv, core LiteX)

| Componente | Driver Zephyr upstream | Note |
|---|---|---|
| VexRiscv (`standard`; poi `secure` con PMP) | board `litex_vexriscv` | Già validato in M0/M1 |
| ROM (boot stub), SRAM, MAIN_RAM | — | La ROM contiene solo lo stub che legge l'immagine già verificata, non il BIOS LiteX |
| UART, timer, GPIO, watchdog, ctrl | `uart_litex`, `timer`, `gpio_litex.c`, `wdt_litex.c` [V] | |
| **SPI master per ADC e memorie** | `spi_litex.c`, `spi_litex_litespi.c` [V] | Requisito di note §2 |
| **Networking** | `eth_litex_liteeth.c` [V]; in alternativa `eth_enc28j60.c` / `eth_enc424j600.c` [V] o W5500 (shield upstream) [V] | LiteEth richiede un PHY (RMII su PMOD): la GateMate A1-EVB ne è sprovvista [da verificare]. Un controller Ethernet su SPI non richiede HDL |
| SPI verso la RoT | LiteSPI + `spi_litex` | Due chip select sullo stesso bus |
| Bus Firewall | — | Previsto (M6) |

### 4.5 Bus di comunicazione tra le due entità

| Opzione | Pro | Contro | Esito |
|---|---|---|---|
| **SPI con `spi_device` di OpenTitan** | Esiste già lato RoT e lato host; due CS: mailbox (framing TPM di TCG PTP, con flow control) e passthrough della flash; driver Zephyr disponibili | Da proteggere contro lo sniffing (§2.2) | **Scelto** |
| I2C | 2 fili | Lento; stessa debolezza degli interposer (TPM Genie) | Scartato |
| UART | Banale | Nessun framing né flow control standard | Solo debug |
| Bridge di bus o memoria condivisa (Wishbone, AXI) | Veloce | Dà all'host accesso diretto alla RoT: **rompe l'isolamento** | Escluso |

Il link si organizza a livelli:

1. **Fisico.** SPI modo 0, host master. Sideband: `HOST_RST_N` (RoT→host), `ROT_IRQ`
   (RoT→host).
2. **Trasporto.** FIFO in stile TPM-over-SPI su CS_TPM. Sul CS_FLASH la RoT filtra i
   comandi della flash: blocca le scritture sulle regioni protette e consente solo letture
   di immagini già verificate.
3. **Messaggio.** `{cmd, seq, len, payload, tag}`. Ogni campo è validato dalla RoT, che
   tratta l'input come ostile.
4. **Servizi.** `GET_RANDOM`, `HASH`, `SIGN` con chiave interna, `ATTEST(nonce)`,
   `GET_MEASUREMENT`, `VERIFY_UPDATE`, `ADVANCE_ROLLBACK`.
5. **Sicurezza del link.**
   - Fasi 1–2: link non autenticato. È accettabile perché il secure boot non dipende dal
     link (la RoT verifica la flash da sola) e nella variante a singolo FPGA il link è
     interno; i servizi runtime vanno però considerati non protetti contro un sonda
     fisica sul link nella variante a due chip.
   - Fase 3: sessione con ECDH verso la chiave pubblica della RoT e MAC su ogni messaggio.
     Copre lo sniffing passivo, cioè l'attacco BitLocker del §2.2.
   - In seguito: allineamento a DMTF SPDM/MCTP, usati da Caliptra e OCP.
   - Nella variante a singolo FPGA il link è interno al fabric e non è sondabile dall'esterno.

### 4.6 Integrazione Zephyr "porta la tua app"

Il generatore emette quattro elementi:

1. La **board Zephyr** (DTS e Kconfig dai CSR LiteX, come in M0).
2. Il **profilo MCUboot** con la chiave pubblica coerente con l'OTP generato.
3. Lo **script di firma** delle immagini.
4. Un **driver PSA Crypto opaco** che traduce `psa_*` in comandi della mailbox.

L'utente ricompila la propria app con `west build -b sencha` e ottiene, senza modificare
il codice:

- secure boot attivo e anti-rollback;
- RNG della RoT;
- per le app che già usano PSA (TLS, MQTT), chiavi che non lasciano la RoT.

Punto aperto: Zephyr basa PSA su Mbed TLS / TF-PSA-Crypto. L'interfaccia dei driver
opachi è ancora in evoluzione e un driver per secure element esterno non risulta
integrato upstream [S, da verificare].

## 5. Elementi di novità

1. **Co-generazione di hardware, chiavi, boot chain e BSP** da un'unica descrizione.
   Mappa di memoria, OTP, chiave pubblica, MCUboot e board Zephyr non possono divergere.
   Nelle soluzioni esistenti sono passi separati, spesso manuali.
2. **RoT attiva e aperta dimensionata per FPGA piccoli** (GateMate, ≈ 20 k elementi
   logici [da verificare]). È un sottoinsieme motivato di OpenTitan, con costo marginale
   misurato in LUT/BRAM anziché in un chip aggiuntivo.
3. **Riutilizzo di `spi_device` come link unico.** Lo stesso blocco fa da mailbox e da
   filtro della flash di boot, e lo stesso modello software vale per FPGA singolo, due
   FPGA o due chip.
4. **Hardening a costo di integrazione nullo per Zephyr** tramite API standard (PSA,
   MCUboot) invece di SDK proprietari.
5. **Valutazione quantitativa** del costo della sicurezza su FPGA a basso costo (O6), un
   dato che la letteratura riporta solo per FPGA grandi (HECTOR-V su Kintex-7).

**Limiti dichiarati:**
- su FPGA non c'è vero OTP;
- le chiavi stanno nel bitstream, salvo cifratura del bitstream: da verificare se la
  GateMate la supporta;
- canali laterali e fault injection sono fuori dal modello di minaccia iniziale, che
  considera un attaccante software remoto e la manomissione della flash.

## 6. Impatto sul piano esistente (`PLAN.md`)

- **O2/O4 (adattatore Wishbone→TL-UL, `hmac` nell'host).** Si sostituiscono con "mini top
  TL-UL della RoT istanziato in LiteX".
- **Risorse GateMate.** Con due CPU, gli IP della RoT e LiteEth il budget di ≈ 20 k
  elementi logici e ≈ 160 KiB di BRAM è stretto. La prima sintesi (M2) deve misurare
  VexRiscv e Ibex da soli prima di aggiungere IP [da verificare].
- **BIOS LiteX.** Nel prodotto non serve: lo sostituisce uno stub che avvia l'immagine
  verificata.

## 7. Bibliografia essenziale

- TCG, *TPM 2.0 Library, Part 1: Architecture*. <https://www.cs.wm.edu/~smherwig/readings/manuals/tcg/tpm2-part1-architecture.pdf> [V]
- J. Boone, *TPM Genie: Interposer Attacks Against the TPM Serial Bus*, NCC Group, 2018. <https://www.nccgroup.com/research/tpm-genie/> [V]
- D. Andzakovic, LPC sniffing of BitLocker keys, 2019; coverage: <https://news.sophos.com/en-us/2019/03/21/researcher-finds-new-way-to-sniff-windows-bitlocker-encryption-keys/> [V]
- WithSecure Labs, *Sniff, there leaks my BitLocker key*. <https://labs.withsecure.com/blog/sniff-there-leaks-my-bitlocker-key> [V]
- D. Moghimi et al., *TPM-FAIL*, USENIX Security 2020. <https://arxiv.org/abs/1911.05673> [V]
- M. Nemec et al., *The Return of Coppersmith's Attack (ROCA)*, ACM CCS 2017. <https://crocs.fi.muni.cz/public/papers/rsa_ccs17> [V]
- H. Jacob et al., *faulTPM: Exposing AMD fTPMs' Deepest Secrets*, 2023. <https://arxiv.org/abs/2304.14717> [V]
- Intel, CVE-2019-0090 whitepaper. <https://www.intel.com/content/dam/www/public/us/en/security-advisory/documents/cve-2019-0090-whitepaper.pdf> [V]
- D. Cerdeira et al., *SoK: … TrustZone-assisted TEE Systems*, IEEE S&P 2020. <https://www.cs.purdue.edu/homes/pfonseca/papers/sp2020-tees.pdf> [V]
- A. Tang et al., *CLKSCREW*, USENIX Security 2017 [V]; P. Qiu et al., *VoltJockey*, ACM CCS 2019 [V]
- M. Lipp et al., *ARMageddon*, USENIX Security 2016 [V]; N. Zhang et al., *TruSpy*, ePrint 2016/980 [V]
- NIST SP 800-193, *Platform Firmware Resiliency Guidelines*, 2018. <https://csrc.nist.gov/pubs/sp/800/193/final> [S]
- P. Nasahl et al., *HECTOR-V*, ACM AsiaCCS 2021. <https://arxiv.org/abs/2009.05262> [V]
- *Unleashing OpenTitan's Potential: a Silicon-Ready Embedded Secure Element…*, 2024. <https://arxiv.org/abs/2406.11558> [V]
- OpenTitan Earl Grey, synthesis report 2024-03-08. <https://reports.opentitan.org/hw/top_earlgrey/syn/2024.03.08_12.46.23/report.html> [V]
- *Area Comparison of CHERIoT and PMP in Ibex*, 2025. <https://arxiv.org/abs/2505.08541> [S]
- Caliptra specification. <https://github.com/chipsalliance/Caliptra> [S]
- PSA Certified, Level 2 + Secure Element. <https://www.psacertified.org/getting-certified/silicon-vendor/overview/level-2-secure-element/> [S]
- Lattice MachXO3D. <https://www.latticesemi.com/Products/FPGAandCPLD/MachXO3D> [S]
- Analog Devices AN-2604 (secure element in BOM). <https://www.analog.com/en/resources/app-notes/an-2604.html> [S]
- Zephyr PSA Crypto. <https://docs.zephyrproject.org/latest/services/crypto/psa_crypto.html> [S]; driver interface PSA: <https://github.com/Mbed-TLS/TF-PSA-Crypto/blob/main/docs/proposed/psa-driver-interface.md> [S]
- SoK su TEE per SoC-FPGA, 2025. <https://arxiv.org/abs/2503.16612> [S]
