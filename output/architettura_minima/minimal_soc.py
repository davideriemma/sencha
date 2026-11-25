#!/usr/bin/env python3

#
# Architettura minima LiteX per il BSP Zephyr (tesi).
#
# Un'unica definizione dell'architettura (ARCH) viene istanziata su due target:
#   - sim      : simulazione Verilator (stessa piattaforma di litex_sim);
#   - gatemate : Olimex GateMate A1-EVB (target litex-boards).
# In questo modo mappa di memoria, CSR e interrupt, cioe' tutto cio' che il BSP Zephyr
# deve conoscere, restano identici tra simulazione e scheda; cambiano solo clock e I/O.
#
# Esempi:
#   ./minimal_soc.py --target sim --run                       # BIOS LiteX in simulazione
#   ./minimal_soc.py --target sim --run --ram-init zephyr.bin # avvio diretto di Zephyr
#   ./minimal_soc.py --target gatemate --run                  # sintesi per la scheda
#   ./minimal_soc.py --target sim --no-compile                # solo Verilog + CSR + overlay
#

import os
import argparse

from migen import *

from litex.gen import *

from litex.build.sim        import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.integration.common   import get_mem_data, get_boot_address
from litex.build.io                 import CRG
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.builder  import Builder

from litex.tools.litex_sim            import _io as sim_io
from litex.tools.litex_json2dts_zephyr import generate_dts_config, _overlay_handlers

# Architettura minima ------------------------------------------------------------------------------

ARCH = dict(
    # CPU: VexRiscv "standard" = RV32IM, cache I/D, 32 linee di interrupt. E' la CPU attesa dal
    # SoC "litex_vexriscv" di Zephyr.
    cpu_type                 = "vexriscv",
    cpu_variant              = "standard",

    # Bus di sistema: Wishbone 32 bit. E' il punto in cui inserire il Bus Firewall.
    bus_standard             = "wishbone",
    bus_data_width           = 32,
    bus_address_width        = 32,

    # CSR a 32 bit: valore predefinito di Zephyr (CONFIG_LITEX_CSR_DATA_WIDTH).
    csr_data_width           = 32,

    # Memorie.
    integrated_rom_size      = 0x2_0000, # 128 KiB, BIOS LiteX (ridimensionata al contenuto).
    integrated_sram_size     = 0x2000,   #   8 KiB, stack/dati del BIOS.
    integrated_main_ram_size = 0x1_0000, #  64 KiB, RAM in cui Zephyr viene caricato ed eseguito.

    # Periferiche richieste da Zephyr.
    with_uart                = True,     # litex,uart           -> console.
    uart_baudrate            = 115200,
    with_timer               = True,     # litex,timer0         -> system tick.
    timer_uptime             = True,     #   registri uptime_*  -> richiesti dal driver timer Zephyr.
    with_ctrl                = True,     # litex,soc-controller -> reset/reboot.
)

# Target: simulazione ------------------------------------------------------------------------------

SIM_CLK_FREQ = int(1e6)

class SimMinimalSoC(SoCCore):
    def __init__(self, **kwargs):
        platform = SimPlatform("SIM", sim_io)
        self.crg = CRG(platform.request("sys_clk"))
        SoCCore.__init__(self, platform, clk_freq=SIM_CLK_FREQ,
            ident     = "Minimal LiteX SoC (sim)",
            uart_name = "sim",
            **kwargs)

def sim_config():
    config = SimConfig()
    config.add_clocker("sys_clk", freq_hz=SIM_CLK_FREQ)
    config.add_module("serial2console", "serial")
    return config

# Target: Olimex GateMate A1-EVB -------------------------------------------------------------------

def gatemate_soc(**kwargs):
    from litex_boards.targets.olimex_gatemate_a1_evb import BaseSoC
    return BaseSoC(sys_clk_freq=24e6, with_led_chaser=False, uart_name="serial", **kwargs)

# Overlay Zephyr -----------------------------------------------------------------------------------

def generate_zephyr_overlay(csr_json, output_dir):
    import json
    with open(csr_json) as f:
        csr = json.load(f)
    dts, config = generate_dts_config(csr, _overlay_handlers)
    with open(os.path.join(output_dir, "overlay.dts"), "w") as f:
        f.write(dts)
    with open(os.path.join(output_dir, "overlay.config"), "w") as f:
        f.write(config)

# Build --------------------------------------------------------------------------------------------

def main():
    here   = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="Architettura minima LiteX per BSP Zephyr.")
    parser.add_argument("--target",      default="sim", choices=["sim", "gatemate"], help="Target.")
    parser.add_argument("--output-dir",  default=None,                               help="Cartella di build (default: build/<target>).")
    parser.add_argument("--run",         action="store_true",                        help="sim: compila ed esegue Verilator; gatemate: esegue la toolchain FPGA.")
    parser.add_argument("--no-compile",  action="store_true",                        help="Non compila BIOS e gateware: genera solo Verilog, CSR e overlay.")
    parser.add_argument("--ram-init",    default=None,                               help="sim: binario (es. zephyr.bin) precaricato in main_ram e avviato dal BIOS.")
    parser.add_argument("--main-ram-size", default=None, type=lambda v: int(v, 0),   help="Dimensione main_ram (default: {:#x}).".format(ARCH["integrated_main_ram_size"]))
    args = parser.parse_args()

    kwargs = dict(ARCH)
    if args.main_ram_size is not None:
        kwargs["integrated_main_ram_size"] = args.main_ram_size

    # SoC.
    if args.target == "sim":
        if args.ram_init is not None:
            kwargs["integrated_main_ram_init"] = get_mem_data(args.ram_init,
                data_width = 32,
                endianness = "little",
                offset     = 0x4000_0000)
        soc = SimMinimalSoC(**kwargs)
        if args.ram_init is not None:
            soc.add_constant("ROM_BOOT_ADDRESS", get_boot_address(args.ram_init) or soc.mem_map["main_ram"])
    else:
        if args.ram_init is not None:
            parser.error("--ram-init e' disponibile solo con --target sim.")
        soc = gatemate_soc(**kwargs)

    # Build.
    output_dir = args.output_dir or os.path.join(here, "build", args.target)
    builder = Builder(soc,
        output_dir       = output_dir,
        compile_software = not args.no_compile,
        compile_gateware = not args.no_compile,
        csr_json         = os.path.join(output_dir, "csr.json"),
        csr_csv          = os.path.join(output_dir, "csr.csv"),
    )
    if args.target == "sim":
        builder.build(sim_config=sim_config(), interactive=True, run=args.run)
    else:
        builder.build(run=args.run)

    # Overlay Zephyr (device tree + Kconfig) ricavato dalla mappa CSR appena generata.
    generate_zephyr_overlay(builder.csr_json, output_dir)

if __name__ == "__main__":
    main()
