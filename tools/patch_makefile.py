import re
import pathlib


def strip_clang_toolchain_overrides(path='kernel/Makefile'):
    p = pathlib.Path(path)
    s = p.read_text()
    before = s
    s = s.replace('CLANG_FLAGS\t+= -no-integrated-as\n', '')
    s = re.sub(r'^CLANG_FLAGS\t\+= --prefix=.*\n', '', s, flags=re.M)
    s = re.sub(r'^CLANG_FLAGS\t\+= --gcc-toolchain=.*\n', '', s, flags=re.M)
    if s != before:
        p.write_text(s)
        print('makefile patched: removed --prefix / --gcc-toolchain / -no-integrated-as')
    else:
        print('makefile already clean')


if __name__ == '__main__':
    strip_clang_toolchain_overrides()
