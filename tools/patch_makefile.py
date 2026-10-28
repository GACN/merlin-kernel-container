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
    # 末尾统一把 -Werror 关掉（老树 + 新编译器有大量新告警）
    if 'KBUILD_CFLAGS += -Wno-error' not in s:
        s += '\n# build fix: old MTK tree vs modern toolchain\nKBUILD_CFLAGS += -Wno-error\n'
    if s != before:
        p.write_text(s)
        print('makefile patched')
    for line in p.read_text().splitlines():
        if 'CLANG_FLAGS' in line and ('prefix' in line or 'integrated' in line):
            print('  ', line.strip())
    print('  tail has -Wno-error:', 'KBUILD_CFLAGS += -Wno-error' in p.read_text())


if __name__ == '__main__':
    patch()
