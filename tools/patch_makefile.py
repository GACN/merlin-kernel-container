import pathlib
import re

PATH = 'kernel/Makefile'


def patch(path=PATH):
    p = pathlib.Path(path)
    s = p.read_text()
    before = s
    # clang + distro binutils: --prefix 必须带 triple，否则会调用宿主 /usr/bin/as
    s = s.replace('CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)',
                  'CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)$(CROSS_COMPILE)')
    s = re.sub(r'^CLANG_FLAGS\t\+= --gcc-toolchain=.*\n', '', s, flags=re.M)
    # 把 -Wno-error 直接塞进 ARCH_CFLAGS/KCFLAGS 那一行（确保在所有 -Werror 之后生效）
    line = 'KBUILD_CFLAGS   += $(ARCH_CFLAGS)   $(KCFLAGS)'
    if line in s and '$(KCFLAGS) -Wno-error' not in s:
        s = s.replace(line, line + ' -Wno-error')
    if s != before:
        p.write_text(s)
        print('makefile patched')
    for l in p.read_text().splitlines():
        if 'CLANG_FLAGS' in l and ('prefix' in l or 'integrated' in l):
            print('  ', l.strip())
        if 'ARCH_CFLAGS' in l and 'KCFLAGS' in l:
            print('  ', l.strip())


if __name__ == '__main__':
    patch()
