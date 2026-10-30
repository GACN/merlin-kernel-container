import pathlib
import re
import subprocess

PATH = 'kernel/Makefile'


def patch_makefile(path=PATH):
    p = pathlib.Path(path)
    s = p.read_text()
    before = s
    # clang + distro binutils: --prefix must carry the triple, otherwise clang
    # invokes the host /usr/bin/as and the build dies on the first .S file.
    s = s.replace('CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)',
                  'CLANG_FLAGS\t+= --prefix=$(GCC_TOOLCHAIN_DIR)$(CROSS_COMPILE)')
    s = re.sub(r'^CLANG_FLAGS\t\+= --gcc-toolchain=.*\n', '', s, flags=re.M)
    line = 'KBUILD_CFLAGS   += $(ARCH_CFLAGS)   $(KCFLAGS)'
    if line in s and '$(KCFLAGS) -Wno-error' not in s:
        s = s.replace(line, line + ' -Wno-error')
    if s != before:
        p.write_text(s)
        print('kernel/Makefile patched')
    else:
        print('kernel/Makefile already patched')


def drop_werror_dirs():
    """Per-directory `subdir-ccflags-y += -Werror` overrides KCFLAGS=-Wno-error."""
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


if __name__ == '__main__':
    patch_makefile()
    drop_werror_dirs()
