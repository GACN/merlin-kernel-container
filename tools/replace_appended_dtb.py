#!/usr/bin/env python3
"""Replace the appended DTB in an Image.gz-dtb with the target phone's stock DTB."""
from __future__ import annotations

import argparse
import gzip
from pathlib import Path
import sys
import zlib


def gzip_end(blob: bytes) -> int:
    dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
    dec.decompress(blob)
    if not dec.eof:
        raise ValueError("kernel gzip stream did not terminate")
    return len(blob) - len(dec.unused_data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("dtb", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    image = args.image.read_bytes()
    dtb = args.dtb.read_bytes()
    if dtb[:4] != b"\xd0\x0d\xfe\xed":
        raise SystemExit(f"{args.dtb}: not a flattened device tree blob")
    end = gzip_end(image)
    if end >= len(image):
        raise SystemExit(f"{args.image}: no appended DTB found")
    args.output.write_bytes(image[:end] + dtb)
    print(f"kernel_gzip_bytes={end}")
    print(f"stock_dtb_bytes={len(dtb)}")
    print(f"output_bytes={args.output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
