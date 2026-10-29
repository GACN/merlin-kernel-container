#!/usr/bin/env python3
"""Patch Linux 4.14 module CRC checks for stock vendor .ko compatibility.

The phone's Wi-Fi/BT modules are prebuilt against the stock Merlin kernel.
The custom kernel keeps CONFIG_MODVERSIONS and the stock vermagic, but the
container config changes can legitimately change symbol CRCs.  Let the kernel
load those modules while retaining the vermagic check.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_modversion_crc.py <kernel-tree>")

path = Path(sys.argv[1]) / "kernel" / "module.c"
text = path.read_text()
if "Droidspaces Merlin MODVERSIONS compatibility" in text:
    print("MODVERSIONS CRC bypass already applied")
    raise SystemExit(0)

pattern = re.compile(
    r"(static int check_version\(const struct load_info \*info,.*?\n\{)"
    r".*?"
    r"(\n\}\n\nstatic inline int check_modstruct_version)",
    re.S,
)
match = pattern.search(text)
if not match:
    raise SystemExit("could not find the expected 4.14 check_version() body")

replacement = (
    match.group(1)
    + "\n"
    + "\t/* Droidspaces Merlin MODVERSIONS compatibility: vendor Wi-Fi/BT "
      "modules use stock CRCs. */\n"
    + "\treturn 1;\n"
    + match.group(2)
)
text = text[:match.start()] + replacement + text[match.end():]
path.write_text(text)
print(f"patched {path}")
