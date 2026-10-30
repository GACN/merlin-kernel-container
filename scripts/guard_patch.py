#!/usr/bin/env python3
"""Add an in-kernel 'do not enter deep suspend' guard to kernel/power/suspend.c.

Why: on this merlinx Pixel port the MTK display / connsys / sensorHub suspend path
deadlocks ~10s after screen-off. The power key then never reaches the input layer
and the MTK watchdog resets the SoC. Holding a wakeup source keeps the SoC in idle
instead of entering that path - the same effect as writing a lock name to
/sys/power/wake_lock, but built into the kernel so no Magisk module is required.

Override at boot with: merlinx_no_suspend=0
"""
import sys

SUSPEND_C = "kernel/power/suspend.c"
INCLUDE_ANCHOR = "#include <linux/suspend.h>"
MARKER = "static const struct platform_suspend_ops *suspend_ops;"

GUARD = r'''
/*
 * merlinx_no_suspend: keep the system out of deep suspend.
 *
 * The MTK display/connsys/sensorHub suspend path on this port deadlocks about
 * 10s after screen-off, after which the power key no longer reaches the input
 * layer and the MTK watchdog resets the device. Holding a wakeup source keeps
 * the SoC in idle instead of entering that path, which is exactly what
 * /sys/power/wake_lock did from userspace, but built in so that no Magisk
 * module is needed. Override at boot with merlinx_no_suspend=0.
 */
static bool merlinx_no_suspend = true;
module_param_named(merlinx_no_suspend, merlinx_no_suspend, bool, 0644);
MODULE_PARM_DESC(merlinx_no_suspend,
		 "Refuse to enter deep system suspend (MTK suspend deadlock workaround)");

static struct wakeup_source *merlinx_guard_ws;

static int __init merlinx_guard_init(void)
{
	if (!merlinx_no_suspend)
		return 0;

	merlinx_guard_ws = wakeup_source_register(NULL, "merlinx_no_suspend_guard");
	if (!merlinx_guard_ws)
		return -ENOMEM;

	__pm_stay_awake(merlinx_guard_ws);
	pr_info("PM: merlinx_no_suspend guard active, deep suspend disabled\n");
	return 0;
}
late_initcall(merlinx_guard_init);
'''


def main() -> int:
    src = open(SUSPEND_C).read()
    if "merlinx_no_suspend" in src:
        print("guard already present, nothing to do")
        return 0

    if INCLUDE_ANCHOR not in src:
        print("ERROR: include anchor %r not found in %s" % (INCLUDE_ANCHOR, SUSPEND_C))
        return 1

    src = src.replace(
        INCLUDE_ANCHOR,
        INCLUDE_ANCHOR + "\n#include <linux/module.h>\n#include <linux/pm_wakeup.h>",
        1,
    )

    if MARKER in src:
        src = src.replace(MARKER, GUARD + "\n" + MARKER, 1)
    else:
        idx = src.index(INCLUDE_ANCHOR) + len(INCLUDE_ANCHOR)
        src = src[:idx] + "\n" + GUARD + "\n" + src[idx:]

    open(SUSPEND_C, "w").write(src)
    print("guard patch applied to %s" % SUSPEND_C)
    return 0


if __name__ == "__main__":
    sys.exit(main())
