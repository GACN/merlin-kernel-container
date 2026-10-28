import pathlib
import re
import subprocess

PATH = 'kernel/Makefile'


def patch_makefile(path=PATH):
    p = pathlib.Path(path)
    s = p.read_text()
    before = s
    # clang + distro binutils：--prefix 必须带 triple，否则会调用宿主 /usr/bin/as
    s = s.replace('CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)',
                  'CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)$(CROSS_COMPILE)')
    s = re.sub(r'^CLANG_FLAGS\t\+= --gcc-toolchain=.*\n', '', s, flags=re.M)
    line = 'KBUILD_CFLAGS   += $(ARCH_CFLAGS)   $(KCFLAGS)'
    if line in s and '$(KCFLAGS) -Wno-error' not in s:
        s = s.replace(line, line + ' -Wno-error')
    if s != before:
        p.write_text(s)
        print('kernel/Makefile patched')


def drop_werror_dirs():
    """mm/Makefile 等目录用 subdir-ccflags-y += -Werror 覆盖全局，逐个改成 -Wno-error"""
    out = subprocess.run(
        ['grep', '-rl', '--', '-Werror', '.'],
        cwd='kernel', capture_output=True, text=True).stdout.split()
    patched = []
    for f in out:
        if not f.endswith(('Makefile', 'Kbuild')):
            continue
        p = pathlib.Path('kernel') / f
        try:
            s = p.read_text()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        new = s.replace('subdir-ccflags-y += -Werror', 'subdir-ccflags-y += -Wno-error')
        new = new.replace('ccflags-y += -Werror', 'ccflags-y += -Wno-error')
        new = new.replace('subdir-ccflags-$(CONFIG_CC_WERROR) += -Werror',
                          'subdir-ccflags-$(CONFIG_CC_WERROR) += -Wno-error')
        if new != s:
            p.write_text(new)
            patched.append(f)
    print('Werror removed in:', ', '.join(patched) or 'none')


def ensure_fw_stub():
    # 公开 OSS 树没带 focaltech 的固件数组，补一个 1 字节占位（运行时走 userspace 请求固件）
    p = pathlib.Path('kernel/include/firmware/fw_sample.i')
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('0x00,\n')
        print('created stub', p)


if __name__ == '__main__':
    patch_makefile()
    drop_werror_dirs()
    ensure_fw_stub()
