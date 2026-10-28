import re
import pathlib

PATH = 'kernel/Makefile'


def patch(path=PATH):
    p = pathlib.Path(path)
    s = p.read_text()
    before = s
    # clang 用 distro binutils 时 --prefix 必须带 triple 前缀，否则会调用 /usr/bin/as
    s = s.replace('CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)',
                  'CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)$(CROSS_COMPILE)')
    s = re.sub(r'^CLANG_FLAGS\t\+= --gcc-toolchain=.*\n', '', s, flags=re.M)
    if s != before:
        p.write_text(s)
        print('makefile patched')
    for line in p.read_text().splitlines():
        if 'CLANG_FLAGS' in line and ('prefix' in line or 'integrated' in line):
            print('  ', line.strip())


if __name__ == '__main__':
    patch()
