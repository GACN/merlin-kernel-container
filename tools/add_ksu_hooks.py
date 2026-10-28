#!/usr/bin/env python3
"""Insert KernelSU v0.9.5 manual hooks into a 4.14 kernel tree.

KernelSU 1.0+ dropped non-GKI support, so a 4.14 kernel must use v0.9.5 with
manual hooks (the kprobe path is an alternative but can bootloop on vendor MTK
kernels). Run after kernel/setup.sh has added drivers/kernelsu.

Usage: add_ksu_hooks.py <kernel_dir>
Exits non-zero if any anchor is missing, so CI fails instead of silently
producing a kernel where su simply does not work.
"""
import re
import sys
import pathlib

MARK = "/* KernelSU manual hooks (added by add_ksu_hooks.py) */"

# (file, regex matching the function definition's first line, extern block, hook body)
PATCHES = [
    (
        "fs/exec.c",
        r"^static int do_execveat_common\(int fd, struct filename \*filename,",
        """#ifdef CONFIG_KSU
extern bool ksu_execveat_hook __read_mostly;
extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr,
			       void *argv, void *envp, int *flags);
extern int ksu_handle_execveat_sucompat(int *fd, struct filename **filename_ptr,
					void *argv, void *envp, int *flags);
#endif
""",
        """#ifdef CONFIG_KSU
	if (unlikely(ksu_execveat_hook))
		ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);
	else
		ksu_handle_execveat_sucompat(&fd, &filename, &argv, &envp, &flags);
#endif
""",
    ),
    (
        "fs/open.c",
        r"^SYSCALL_DEFINE3\(faccessat, int, dfd, const char __user \*, filename, int, mode\)",
        """#ifdef CONFIG_KSU
extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user,
				int *mode, int *flags);
#endif
""",
        """#ifdef CONFIG_KSU
	ksu_handle_faccessat(&dfd, &filename, &mode, NULL);
#endif
""",
    ),
    (
        "fs/read_write.c",
        r"^ssize_t vfs_read\(struct file \*file, char __user \*buf, size_t count, loff_t \*pos\)",
        """#ifdef CONFIG_KSU
extern bool ksu_vfs_read_hook __read_mostly;
extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr,
			       size_t *count_ptr, loff_t **pos);
#endif
""",
        """#ifdef CONFIG_KSU
	if (unlikely(ksu_vfs_read_hook))
		ksu_handle_vfs_read(&file, &buf, &count, &pos);
#endif
""",
    ),
    (
        "fs/stat.c",
        r"^int vfs_statx\(int dfd, const char __user \*filename, int flags,",
        """#ifdef CONFIG_KSU
extern int ksu_handle_stat(int *dfd, const char __user **filename_user, int *flags);
#endif
""",
        """#ifdef CONFIG_KSU
	ksu_handle_stat(&dfd, &filename, &flags);
#endif
""",
    ),
]


def patch_file(root: pathlib.Path, rel: str, def_re: str, externs: str, body: str) -> str:
    path = root / rel
    text = path.read_text()
    lines = text.splitlines(keepends=True)

    if "ksu_handle_" in text:
        return f"{rel}: already patched"

    idx = None
    for i, line in enumerate(lines):
        if re.search(def_re, line):
            idx = i
            break
    if idx is None:
        raise SystemExit(f"ERROR: anchor not found in {rel}: {def_re}")

    # find the opening brace of the function body
    brace = None
    for j in range(idx, min(idx + 12, len(lines))):
        if lines[j].strip() == "{":
            brace = j
            break
    if brace is None:
        raise SystemExit(f"ERROR: opening brace not found for anchor in {rel}")

    lines.insert(brace + 1, body)
    lines.insert(idx, MARK + "\n" + externs)
    path.write_text("".join(lines))
    return f"{rel}: hooked (def line {idx + 1})"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: add_ksu_hooks.py <kernel_dir>")
    root = pathlib.Path(sys.argv[1])
    if not (root / "fs" / "exec.c").is_file():
        raise SystemExit(f"ERROR: {root} does not look like a kernel tree")
    for rel, def_re, externs, body in PATCHES:
        print(patch_file(root, rel, def_re, externs, body))


if __name__ == "__main__":
    main()
