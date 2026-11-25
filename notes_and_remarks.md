# Notes and Remarks

## 2026-11-24
add some detail to a couple of examples for RoT
## 2026-11-24 — Decisioni architettura RoT
1. RoT core -> Ibex (core separato dall'host, stile OpenTitan/Caliptra)
2. Chip principale (host): deve includere una periferica SPI master per ADC esterni / memorie (oltre alla SPI flash di boot)
3. Chip principale: auspicabilmente una parte di networking (Ethernet via LiteEth come prima scelta; valutare in seguito alternative wireless tramite modulo esterno)
