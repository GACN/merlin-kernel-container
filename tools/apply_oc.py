#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


REL = Path("drivers/misc/mediatek/base/power/cpufreq_v1/src/mach/mt6768/mtk_cpufreq_opp_table.h")
OLD = "#define CPU_DVFS_FREQ0_L_6768\t\t2000000"
NEW = "#define CPU_DVFS_FREQ0_L_6768\t\t2300000"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("kernel", type=Path)
    args = ap.parse_args()
    path = args.kernel / REL
    text = path.read_text()
    count = text.count(OLD)
    if count != 1:
        raise SystemExit(f"expected exactly one stock OC anchor in {path}, found {count}")
    path.write_text(text.replace(OLD, NEW, 1))
    print(f"patched {path}: 2.000 GHz -> 2.300 GHz big-cluster OPP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
